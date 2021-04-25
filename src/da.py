from domain import *
import pymysql
import os

class Dao:
    PLAYER_SQL_PREFIX = """
        select u.ID, u.NAME, u.EMAIL, u.PHONE_NUMBER, u.PHOTO_URL, u.AVAILABILITY_TEXT, u.ADMIN, l.ID as LADDER_ID, p.SCORE, p.EARNED_POINTS, p.BORROWED_POINTS,
          (select count(distinct SCORE) + 1 from players_vw where LADDER_ID = %s and SCORE > p.SCORE) as RANKING,
          (select count(*) as WINS from matches where LADDER_ID = %s and WINNER_ID = u.ID) as WINS,
          (select count(*) as WINS from matches where LADDER_ID = %s and LOSER_ID = u.ID) as LOSSES
        from players_vw p
        join users u
            on p.USER_ID = u.ID
        join ladders l
            on p.LADDER_ID = l.ID
        where l.ID = %s
    """
    PLAYERS_SQL_POSTFIX = " order by p.SCORE desc "
    PLAYER_SQL_POSTFIX = " and p.USER_ID = %s"
    PLAYERS_SQL = PLAYER_SQL_PREFIX + PLAYERS_SQL_POSTFIX
    PLAYER_SQL = PLAYER_SQL_PREFIX + PLAYER_SQL_POSTFIX

    def __init__(self):
        try:
            self.conn = pymysql.connect(os.environ["DB_HOST"], user = (os.environ["DB_USERNAME"]), passwd = (os.environ["DB_PASSWORD"]), db = (os.environ["DB_DATABASE_NAME"]), autocommit = True)
        except Exception as e:
            print("ERROR: Could not connect to MySQL", e)
            raise ServiceException("Failed to connect to database")

    def get_user(self, user_id):
        return self.get_one(User, "select ID, NAME, EMAIL, PHONE_NUMBER, PHOTO_URL, AVAILABILITY_TEXT, ADMIN from users where ID = %s", user_id)

    def in_same_ladder(self, user1_id, user2_id):
        return self.get_one(bool, "select count(*) > 0 as IN_SAME_LADDER from ladders l join players p1 on l.ID = p1.LADDER_ID and p1.USER_ID = %s join players p2 on l.ID = p2.LADDER_ID and p2.USER_ID = %s", user1_id, user2_id)

    def create_user(self, user):
        self.insert("insert into users (ID, NAME, EMAIL, PHONE_NUMBER, PHOTO_URL, AVAILABILITY_TEXT) values (%s, %s, %s, %s, %s, %s)", user.user_id, user.name, user.email, user.phone_number, user.photo_url, user.availability_text)

    def update_user(self, user):
        self.execute("update users set NAME = %s, EMAIL = %s, PHONE_NUMBER = %s, PHOTO_URL = %s, AVAILABILITY_TEXT = %s where ID = %s", user.name, user.email, user.phone_number, user.photo_url, user.availability_text, user.user_id)

    def get_ladders(self):
        return self.get_list(Ladder, "select ID, NAME, START_DATE, END_DATE, DISTANCE_PENALTY_ON from ladders order by START_DATE DESC")

    def get_ladder(self, ladder_id):
        return self.get_one(Ladder, "select ID, NAME, START_DATE, END_DATE, DISTANCE_PENALTY_ON from ladders where ID = %s", ladder_id)

    def get_players(self, ladder_id):
        return self.get_list(Player, self.PLAYERS_SQL, ladder_id, ladder_id, ladder_id, ladder_id)

    def get_player(self, ladder_id, user_id):
        return self.get_one(Player, self.PLAYER_SQL, ladder_id, ladder_id, ladder_id, ladder_id, user_id)

    def create_player(self, ladder_id, user_id):
        self.execute("insert into players (USER_ID, LADDER_ID) values (%s, %s)", user_id, ladder_id)

    def update_borrowed_points(self, ladder_id, user_id, new_borrowed_points):
        self.execute("UPDATE players set BORROWED_POINTS = %s where LADDER_ID = %s and USER_ID = %s", new_borrowed_points, ladder_id, user_id)

    def update_earned_points(self, ladder_id, user_id, new_points_to_add):
        self.execute("UPDATE players set EARNED_POINTS = EARNED_POINTS + %s where LADDER_ID = %s and USER_ID = %s", new_points_to_add, ladder_id, user_id)

    def get_matches(self, ladder_id, user_id = None):
        sql_prefix = "select ID, LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE from matches where LADDER_ID = %s"
        sql_postfix = " order by MATCH_DATE desc"

        if user_id is not None:
            sql_prefix += " and (WINNER_ID = %s or LOSER_ID = %s)"
            return self.get_list(Match, sql_prefix + sql_postfix, ladder_id, user_id, user_id)
        else:
            return self.get_list(Match, sql_prefix + sql_postfix, ladder_id)

    def get_match(self, match_id) -> Match:
        return self.get_one(Match, "select ID, LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE, WINNER_POINTS, LOSER_POINTS from matches where ID = %s", match_id)

    def create_match(self, match):
        match_id = self.insert("insert into matches (LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE, WINNER_POINTS, LOSER_POINTS) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", *match.get_insert_properties())
        return self.get_one(Match, "select ID, LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE from matches where ID = %s", match_id)

    def update_match(self, match: Match):
        self.execute("update matches set LADDER_ID = %s, MATCH_DATE = %s, WINNER_ID = %s, LOSER_ID = %s, WINNER_SET1_SCORE = %s, LOSER_SET1_SCORE = %s, WINNER_SET2_SCORE = %s, LOSER_SET2_SCORE = %s, WINNER_SET3_SCORE = %s, LOSER_SET3_SCORE = %s, WINNER_POINTS = %s, LOSER_POINTS = %s where ID = %s", match.ladder_id, match.match_date, match.winner_id, match.loser_id, match.winner_set1_score, match.loser_set1_score, match.winner_set2_score, match.loser_set2_score, match.winner_set3_score, match.loser_set3_score, match.winner_points, match.loser_points, match.match_id)

    def get_ladder_code(self, ladder_id):
        return self.get_one(str, "select CODE from ladder_codes where LADDER_ID = %s", ladder_id)

    ### UTILS ###

    def get_list(self, klass, sql, *args):
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, args)
                results = []
                for row in cur.fetchall():
                    results.append(klass(*row))
                return results
        except Exception as e:
            print(e)
            raise ServiceException("Error getting data from database")

    def get_one(self, klass, sql, *args):
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, args)
                row = cur.fetchone()
                if row is not None:
                    return klass(*row)
                return None
        except Exception as e:
            print(e)
            raise ServiceException("Error getting data from database")

    def insert(self, sql, *args):
        try:
            with self.conn.cursor() as cur:
                cur.execute(sql, args)
                return cur.lastrowid
        except Exception as e:
            print(e)
            raise ServiceException("Error inserting data into database")

    def execute(self, sql, *args):
        try:
            with self.conn.cursor() as cur:
                affected_rows = cur.execute(sql, args)
                print(sql, args, affected_rows)
        except Exception as e:
            print(e)
            raise ServiceException("Error executing database command")
