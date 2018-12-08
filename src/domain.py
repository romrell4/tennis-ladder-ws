class User:
    def __init__(self, user_id, name, email, photo_url):
        self.user_id, self.name, self.email, self.photo_url = user_id, name, email, photo_url

class Ladder:
    def __init__(self, ladder_id, name, start_date, end_date):
        self.ladder_id, self.name, self.start_date, self.end_date = ladder_id, name, str(start_date), str(end_date)

class Score:
    def __init__(self, user_id, ladder_id, score):
        self.user_id, self.ladder_id, self.score = user_id, ladder_id, score

class Match:
    def __init__(self, match_id, ladder_id, match_date, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score = None, loser_set3_score = None):
        self.match_id, self.ladder_id, self.match_date, self.winner_id, self.loser_id, self.winner_set1_score, self.loser_set1_score, self.winner_set2_score, self.loser_set2_score, self.winner_set3_score, self.loser_set3_score = match_id, ladder_id, match_date, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score, loser_set3_score

    def validate(self):
        if self.winner_id is None: raise DomainException("Missing winner_id")
        if self.loser_id is None: raise DomainException("Missing loser_id")

        if not Match.is_valid_set(self.winner_set1_score, self.loser_set1_score) or \
                not Match.is_valid_set(self.winner_set2_score, self.loser_set2_score) or \
                (self.winner_set3_score is None and self.loser_set3_score is None) or \
                (not Match.is_valid_set(self.winner_set3_score, self.loser_set3_score) and Match.is_valid_tiebreak(self.winner_set3_score, self.loser_set3_score)):
            raise DomainException("Invalid set scores")
        return self

    @staticmethod
    def is_valid_set(winner_score, loser_score):
        # TODO: Mark
        pass

    @staticmethod
    def is_valid_tiebreak(winner_score, loser_score):
        # TODO: Mark
        pass

    def calculate_scores(self):
        # TODO: Mark
        pass

    @staticmethod
    def calculate_distance_penalty(winner_rank, loser_rank):
        # TODO: Mark
        pass

    def get_insert_properties(self):
        return [self.winner_id, self.loser_id, self.winner_set1_score, self.loser_set1_score, self.winner_set2_score, self.loser_set2_score, self.winner_set3_score, self.loser_set3_score]

#### Non-DB Objects ####

class Player:
    def __init__(self, user_id, ladder_id, name, score):
        self.user_id, self.ladder_id, self.name, self.score = user_id, ladder_id, name, score

class ServiceException(Exception):
    def __init__(self, message, status_code = 500):
        self.error_message = message
        self.status_code = status_code

class DomainException(ServiceException):
    MESSAGE_FORMAT = "Invalid request. {}"

    def __init__(self, message):
        super().__init__(DomainException.MESSAGE_FORMAT.format(message), 400)
