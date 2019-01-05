import math

class User:
    def __init__(self, user_id, name, email, photo_url):
        self.user_id, self.name, self.email, self.photo_url = user_id, name, email, photo_url

    def get_insert_properties(self):
        return [self.user_id, self.name, self.email, self.photo_url]

class Ladder:
    def __init__(self, ladder_id, name, start_date, end_date):
        self.ladder_id, self.name, self.start_date, self.end_date = ladder_id, name, str(start_date), str(end_date)

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
            match_dict.get("winner").get("user_id") if "winner" in match_dict else None,
            match_dict.get("loser").get("user_id") if "loser" in match_dict else None,
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

        if not Match.is_valid_set(self.winner_set1_score, self.loser_set1_score) or \
                not Match.is_valid_set(self.winner_set2_score, self.loser_set2_score) or \
                (self.winner_set3_score is not None and self.loser_set3_score is not None and not Match.is_valid_set(self.winner_set3_score, self.loser_set3_score) and not Match.is_valid_tiebreak(self.winner_set3_score, self.loser_set3_score)):
            raise DomainException("Invalid set scores")
        return self

    @staticmethod
    def is_valid_set(winner_score, loser_score):
        # TODO: Mark
        return True

    @staticmethod
    def is_valid_tiebreak(winner_score, loser_score):
        # TODO: Mark
        return True

    def calculate_scores(self, winner_rank, loser_rank):
        loser_score = self.loser_set1_score + self.loser_set2_score
        if self.loser_set3_score is not None:
            # If a tiebreak, half of the score - rounded up. Otherwise, just the score. However, you can never get more than 6 point for a tiebreak
            loser_score += min(int(math.ceil(self.loser_set3_score / 2)) if self.played_tiebreak() else self.loser_set3_score, Match.MAX_TIEBREAK_POINTS)

        # The winners score cannot go below zero (if there is a large distance penalty)
        winner_score = max(Match.BASE_WINNER_POINTS - loser_score - self.calculate_distance_penalty(winner_rank, loser_rank), Match.MIN_WINNER_POINTS)
        return winner_score, loser_score

    def played_tiebreak(self):
        return self.winner_set3_score is not None and self.loser_set3_score is not None and max(self.winner_set3_score, self.loser_set3_score) >= Match.MIN_TIEBREAK_WINNER_SCORE

    @staticmethod
    def calculate_distance_penalty(winner_rank, loser_rank):
        return (winner_rank - loser_rank) * Match.DISTANCE_PENALTY_MULTIPLIER

    def get_insert_properties(self):
        return [self.ladder_id, self.match_date, self.winner_id, self.loser_id, self.winner_set1_score, self.loser_set1_score, self.winner_set2_score, self.loser_set2_score, self.winner_set3_score, self.loser_set3_score]

#### Non-DB Objects ####

class Player:
    def __init__(self, user_id, ladder_id, name, photo_url, score, ranking, wins, losses):
        self.user_id, self.ladder_id, self.name, self.photo_url, self.score, self.ranking, self.wins, self.losses = user_id, ladder_id, name, photo_url, score, ranking, wins, losses

class ServiceException(Exception):
    def __init__(self, message, status_code = 500):
        self.error_message = message
        self.status_code = status_code

class DomainException(ServiceException):
    MESSAGE_FORMAT = "Invalid request. {}"

    def __init__(self, message):
        super().__init__(DomainException.MESSAGE_FORMAT.format(message), 400)
