import math

class User:
    def __init__(self, user_id, name, email, phone_number, photo_url):
        self.user_id, self.name, self.email, self.phone_number, self.photo_url = user_id, name, email, phone_number, photo_url

    def get_insert_properties(self):
        return [self.user_id, self.name, self.email, self.phone_number, self.photo_url]

class Ladder:
    def __init__(self, ladder_id, name, start_date, end_date, distance_penalty_on):
        self.ladder_id, self.name, self.start_date, self.end_date, self.distance_penalty_on = ladder_id, name, start_date, end_date, distance_penalty_on

class Match:
    BASE_WINNER_POINTS = 39
    MIN_WINNER_POINTS = 0
    MAX_TIEBREAK_POINTS = 6
    MIN_TIEBREAK_WINNER_SCORE = 10
    DISTANCE_PENALTY_MULTIPLIER = -3

    def __init__(self, match_id, ladder_id, match_date, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score = None, loser_set3_score = None):
        self.match_id, self.ladder_id, self.match_date, self.winner_id, self.loser_id, self.winner_set1_score, self.loser_set1_score, self.winner_set2_score, self.loser_set2_score, self.winner_set3_score, self.loser_set3_score = match_id, ladder_id, match_date, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score, loser_set3_score

    @staticmethod
    def from_dict(match_dict):
        return Match(
            match_dict.get("match_id"),
            match_dict.get("ladder_id"),
            match_dict.get("match_date"),
            match_dict.get("winner", {}).get("user", {}).get("user_id"),
            match_dict.get("loser", {}).get("user", {}).get("user_id"),
            match_dict.get("winner_set1_score"),
            match_dict.get("loser_set1_score"),
            match_dict.get("winner_set2_score"),
            match_dict.get("loser_set2_score"),
            match_dict.get("winner_set3_score"),
            match_dict.get("loser_set3_score")
        ).validate()

    def validate(self):
        if self.ladder_id is None: raise DomainException("Missing ladder_id")
        if self.winner_id is None: raise DomainException("Missing winner's user_id")
        if self.loser_id is None: raise DomainException("Missing loser's user_id")
        if self.winner_id == self.loser_id: raise DomainException("A match cannot be played against oneself")

        if not Match.is_valid_set(self.winner_set1_score, self.loser_set1_score):
            raise DomainException("Invalid scores for set 1")
        elif not Match.is_valid_set(self.winner_set2_score, self.loser_set2_score):
            raise DomainException("Invalid scores for set 2")
        elif self.winner_set3_score is not None and self.loser_set3_score is not None:
            if not Match.is_valid_set(self.winner_set3_score, self.loser_set3_score) and not Match.is_valid_tiebreak(self.winner_set3_score, self.loser_set3_score):
                raise DomainException("Invalid scores for set 3")

            # Check if the same person won all three sets
            set_scores = [
                [self.winner_set1_score, self.loser_set1_score],
                [self.winner_set2_score, self.loser_set2_score],
                [self.winner_set3_score, self.loser_set3_score]
            ]
            set_winners = [set_score[0] > set_score[1] for set_score in set_scores]

            if len(set(set_winners)) == 1:
                raise DomainException("Invalid scores. This is a best 2 out of 3 set format. One player cannot win all three sets.")

        return self

    @staticmethod
    def is_valid_set(winner_score, loser_score):
        if winner_score is None or loser_score is None: return False
        set_loser_score, set_winner_score = sorted([winner_score, loser_score])
        return (set_winner_score == 7 and 5 <= set_loser_score <= 6) or (set_winner_score == 6 and 0 <= set_loser_score <= 4)

    @staticmethod
    def is_valid_tiebreak(winner_score, loser_score):
        if winner_score is None or loser_score is None: return False
        return (winner_score == 10 and 0 <= loser_score <= 8) or (winner_score > 10 and loser_score == winner_score - 2)

    def calculate_scores(self, winner_rank, loser_rank, distance_penalty_on):
        loser_score = self.loser_set1_score + self.loser_set2_score
        if self.loser_set3_score is not None:
            # If a tiebreak, half of the score - rounded up. Otherwise, just the score. However, you can never get more than 6 point for a tiebreak
            loser_score += min(int(math.ceil(self.loser_set3_score / 2)) if self.played_tiebreak() else self.loser_set3_score, Match.MAX_TIEBREAK_POINTS)

        # The winners score cannot go below zero (if there is a large distance penalty)
        winner_score = max(Match.BASE_WINNER_POINTS - loser_score - self.calculate_distance_penalty(winner_rank, loser_rank, distance_penalty_on), Match.MIN_WINNER_POINTS)
        return winner_score, loser_score

    def played_tiebreak(self):
        return self.winner_set3_score is not None and self.loser_set3_score is not None and max(self.winner_set3_score, self.loser_set3_score) >= Match.MIN_TIEBREAK_WINNER_SCORE

    @staticmethod
    def calculate_distance_penalty(winner_rank, loser_rank, distance_penalty_on):
        return (winner_rank - loser_rank) * Match.DISTANCE_PENALTY_MULTIPLIER if distance_penalty_on else 0

    def get_insert_properties(self):
        return [self.ladder_id, self.match_date, self.winner_id, self.loser_id, self.winner_set1_score, self.loser_set1_score, self.winner_set2_score, self.loser_set2_score, self.winner_set3_score, self.loser_set3_score]

#### Non-DB Objects ####

class Player:
    def __init__(self, user_id, name, email, phone_number, photo_url, ladder_id, score, ranking, wins, losses):
        self.user, self.ladder_id, self.score, self.ranking, self.wins, self.losses = User(user_id, name, email, phone_number, photo_url), ladder_id, score, ranking, wins, losses

class ServiceException(Exception):
    def __init__(self, message, status_code = 500):
        self.error_message = message
        self.status_code = status_code

class DomainException(ServiceException):
    def __init__(self, message):
        super().__init__(message, 400)
