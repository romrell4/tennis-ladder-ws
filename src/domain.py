class User:
    def __init__(self, user_id, name):
        self.user_id, self.name = user_id, name

class Ladder:
    def __init__(self, ladder_id, name, start_date, end_date):
        self.ladder_id, self.name, self.start_date, self.end_date = ladder_id, name, str(start_date), str(end_date)

class Score:
    def __init__(self, user_id, ladder_id, score):
        self.user_id, self.ladder_id, self.score = user_id, ladder_id, score

class Match:
    def __init__(self, match_id, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score, loser_set3_score):
        self.match_id, self.winner_id, self.loser_id, self.winner_set1_score, self.loser_set1_score, self.winner_set2_score, self.loser_set2_score, self.winner_set3_score, self.loser_set3_score = match_id, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score, loser_set3_score

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
