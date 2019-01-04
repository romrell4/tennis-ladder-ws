from domain import *
import pymysql
import os

class Dao:
    PLAYER_SQL_PREFIX = """
        select u.ID as USER_ID, l.ID as LADDER_ID, u.NAME, u.PHOTO_URL, p.SCORE,
          (select count(*) + 1 from players where SCORE > p.SCORE) as RANKING,
          (select count(*) as WINS from matches where WINNER_ID = u.ID) as WINS,
          (select count(*) as WINS from matches where LOSER_ID = u.ID) as LOSSES
        from players p
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
        return self.get_one(User, "SELECT * FROM users where ID = %s", user_id)

    def create_user(self, user):
        self.insert("INSERT INTO users (ID, NAME, EMAIL, PHOTO_URL) values (%s, %s, %s, %s)", *user.get_insert_properties())

    def get_ladders(self):
        return self.get_list(Ladder, "SELECT * FROM ladders ORDER BY START_DATE DESC")

    def get_ladder(self, ladder_id):
        return self.get_one(Ladder, "select * from ladders where ID = %s", ladder_id)

    def get_players(self, ladder_id):
        return self.get_list(Player, self.PLAYERS_SQL, ladder_id)

    def get_player(self, ladder_id, user_id):
        return self.get_one(Player, self.PLAYER_SQL, ladder_id, user_id)

    def get_matches(self, ladder_id, user_id):
        return self.get_list(Match, "SELECT * FROM matches where LADDER_ID = %s and (WINNER_ID = %s or LOSER_ID = %s)", ladder_id, user_id, user_id)

    def create_match(self, match):
        match_id = self.insert("INSERT INTO matches (LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", *match.get_insert_properties())
        return self.get_one(Match, "SELECT * FROM matches WHERE ID = %s", match_id)

    def update_score(self, user_id, ladder_id, new_score_to_add):
        self.execute("UPDATE players SET SCORE = SCORE + %s WHERE USER_ID = %s and LADDER_ID = %s", new_score_to_add, user_id, ladder_id)

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
                cur.execute(sql, args)
        except Exception as e:
            print(e)
            raise ServiceException("Error executing database command")
