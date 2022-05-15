from datetime import datetime, date

from domain import User, Match, Player, Ladder


def ladder(ladder_id=0, name="", start_date=date.today(), end_date=date.today(), distance_penalty_on=False, weeks_for_borrowed_points=0, weeks_for_borrowed_points_left=0, logged_in_user_has_joined=False) -> Ladder:
    return Ladder(ladder_id, name, start_date, end_date, distance_penalty_on, weeks_for_borrowed_points, weeks_for_borrowed_points_left, logged_in_user_has_joined)


def match(match_id=0, ladder_id=0, match_date: datetime = datetime.now(), winner_id="", loser_id="",
          winner_set1_score=0, loser_set1_score=0, winner_set2_score=0, loser_set2_score=0, winner_set3_score=None, loser_set3_score=None, winner_points=0, loser_points=0) -> Match:
    return Match(match_id, ladder_id, match_date, winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score, loser_set3_score, winner_points, loser_points)


def user(user_id="", name="", email="", phone_number=None, photo_url=None, availability_text=None, admin=False) -> User:
    return User(user_id, name, email, phone_number, photo_url, availability_text, admin)


def player(user_: User = user(), ladder_id=0, score=0, earned_points=0, borrowed_points=0, ranking=0, wins=0, losses=0) -> Player:
    return Player(user_.user_id, user_.name, user_.email, user_.phone_number, user_.photo_url, user_.availability_text, user_.admin, ladder_id, score, earned_points, borrowed_points, ranking, wins, losses)
