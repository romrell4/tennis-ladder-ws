import os
import unittest
from datetime import date

import properties
from da import DaoImpl
from domain import *


class Test(unittest.TestCase):
    dao: DaoImpl
    mountain_tz = timezone("US/Mountain")

    @classmethod
    def setUpClass(cls):
        os.environ["DB_HOST"] = properties.db_host
        os.environ["DB_USERNAME"] = properties.db_username
        os.environ["DB_PASSWORD"] = properties.db_password
        os.environ["DB_DATABASE_NAME"] = properties.db_database_name

        cls.dao = DaoImpl()

    def setUp(self) -> None:
        # noinspection PyBroadException
        try:
            self.dao.insert("""INSERT INTO users (ID, NAME, EMAIL, PHONE_NUMBER, PHOTO_URL, AVAILABILITY_TEXT) VALUES 
                ('TEST1', 'Tester One', 'test1@mail.com', '111-111-1111', 'test1.jpg', 'avail 1'),
                ('TEST2', 'Tester Two', 'test2@mail.com', null, 'test2.jpg', 'avail 2'),
                ('TEST3', 'Tester Three', 'test3@mail.com', null, 'test3.jpg', 'avail 3'),
                ('TEST4', 'Tester Four', 'test4@mail.com', null, 'test4.jpg', 'avail 4'),
                ('TEST5', 'Tester Five', 'test4@mail.com', null, 'test5.jpg', 'avail 5')
            """)
            self.dao.insert("""INSERT INTO ladders (ID, NAME, START_DATE, END_DATE, PASSCODE) VALUES 
                (-3, 'Test 1', DATE '2018-01-01', DATE '2018-01-02', 'good'),
                (-4, 'Test 2', DATE '2018-02-01', DATE '2018-02-02', ''),
                (-5, 'Test 3', DATE '2018-01-02', DATE '2018-01-03', '')
            """)
            self.dao.insert("""INSERT INTO players (USER_ID, LADDER_ID, EARNED_POINTS, BORROWED_POINTS, `ORDER`) VALUES
                ('TEST1', -3, 5, 0, 0),
                ('TEST2', -3, 10, 0, 0),
                ('TEST3', -3, 10, 0, 0),
                ('TEST1', -4, 0, 0, 1),
                ('TEST4', -4, 0, 0, 2),
                ('TEST2', -5, 0, 30, 1)
            """)
            self.dao.insert("""INSERT INTO matches (ID, LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE, WINNER_POINTS, LOSER_POINTS) VALUES 
                (-1, -3, '2018-01-02 03:04:05', 'TEST1', 'TEST2', 6, 0, 0, 6, 7, 5, 28, 11)
            """)
            self.dao.insert("""INSERT INTO ladder_admins (LADDER_ID, USER_ID) VALUES
                (-3, 'TEST1'),
                (-3, 'TEST2')
            """)
        except Exception:
            self.tearDown()
            exit()

    def tearDown(self) -> None:
        # These will cascade in order to delete the other ones
        self.dao.execute("DELETE FROM users where ID in ('__TEST', 'TEST1', 'TEST2', 'TEST3', 'TEST4', 'TEST5')")
        self.dao.execute("DELETE FROM ladders where ID in (-3, -4, -5)")

    def test_get_user(self):
        # Test non-existent user
        user = self.dao.get_user("TEST0")
        self.assertIsNone(user)

        # Test regular user
        user = self.dao.get_user("TEST1")
        self.assertIsNotNone(user)
        self.assertEqual("TEST1", user.user_id)
        self.assertEqual("Tester One", user.name)
        self.assertEqual("test1@mail.com", user.email)
        self.assertEqual("111-111-1111", user.phone_number)
        self.assertEqual("test1.jpg", user.photo_url)
        self.assertEqual("avail 1", user.availability_text)

    def test_in_same_ladder(self):
        self.assertFalse(self.dao.in_same_ladder("TEST1", "TEST0"))
        self.assertFalse(self.dao.in_same_ladder("TEST0", "TEST1"))
        self.assertTrue(self.dao.in_same_ladder("TEST1", "TEST1"))
        self.assertFalse(self.dao.in_same_ladder("TEST2", "TEST4"))
        self.assertTrue(self.dao.in_same_ladder("TEST1", "TEST4"))

    def test_create_user(self):
        self.dao.create_user(User("__TEST", "Tester", "test@test.com", "123-456-7890", "test.jpg", "avail", True))
        user = self.dao.get_one(User, "SELECT ID, NAME, EMAIL, PHONE_NUMBER, PHOTO_URL, AVAILABILITY_TEXT, ADMIN FROM users where ID = '__TEST'")
        self.assertIsNotNone(user)
        self.assertEqual("__TEST", user.user_id)
        self.assertEqual("Tester", user.name)
        self.assertEqual("test@test.com", user.email)
        self.assertEqual("123-456-7890", user.phone_number)
        self.assertEqual("test.jpg", user.photo_url)
        self.assertEqual("avail", user.availability_text)
        # Create user doesn't allow setting admin status
        self.assertEqual(False, user.admin)

    def test_update_user(self):
        sql = "select ID, NAME, EMAIL, PHONE_NUMBER, PHOTO_URL, AVAILABILITY_TEXT, ADMIN from users where ID = 'TEST1'"
        new_user = User('TEST1', "new name", "new email", "new phone", "new photo", "new availability", True)

        self.dao.update_user(new_user)
        saved_user = self.dao.get_one(User, sql)
        self.assertEqual("new name", saved_user.name)
        self.assertEqual("new email", saved_user.email)
        self.assertEqual("new phone", saved_user.phone_number)
        self.assertEqual("new photo", saved_user.photo_url)
        self.assertEqual("new availability", saved_user.availability_text)
        # Update user doesn't allow setting admin status
        self.assertEqual(False, saved_user.admin)

    def test_get_ladders(self):
        # Test running the SQL and creating the objects
        ladders = self.dao.get_ladders()
        self.assertIsNotNone(ladders)
        self.assertGreater(len(ladders), 0)

        # Test that the values deserialized correctly, and that they were ordered correctly
        ladder = next(filter(lambda x: x.ladder_id < 0, ladders), None)
        self.assertIsNotNone(ladder)
        self.assertEqual(-4, ladder.ladder_id)
        self.assertEqual("Test 2", ladder.name)
        self.assertEqual(date(2018, 2, 1), ladder.start_date)
        self.assertEqual(date(2018, 2, 2), ladder.end_date)
        self.assertFalse(ladder.distance_penalty_on)

    def test_get_ladder(self):
        # Test a ladder that doesn't exist
        ladder = self.dao.get_ladder(0)
        self.assertIsNone(ladder)

        # Test a normal ladder
        ladder = self.dao.get_ladder(-3)
        self.assertIsNotNone(ladder)

    def test_get_ladder_admins(self):
        # Test a ladder with admins
        admins = self.dao.get_ladder_admins(-3)
        self.assertEqual(len(admins), 2)

        # Test a ladder without admins
        admins = self.dao.get_ladder_admins(-4)
        self.assertEqual(len(admins), 0)

    def test_update_ladder_only_updates_weeks_for_borrowed_points_left(self):
        ladder_id = -3
        old_ladder = self.dao.get_ladder(ladder_id)

        # Change everything about the ladder
        proposed_ladder = Ladder(
            ladder_id=old_ladder.ladder_id,
            name="New",
            start_date=datetime.today(),
            end_date=datetime.today(),
            distance_penalty_on=True,
            weeks_for_borrowed_points=5,
            weeks_for_borrowed_points_left=5,
        )
        self.dao.update_ladder(proposed_ladder)
        new_ladder = self.dao.get_ladder(ladder_id)

        # These fields shouldn't change
        self.assertEqual(old_ladder.ladder_id, new_ladder.ladder_id)
        self.assertEqual(old_ladder.name, new_ladder.name)
        self.assertEqual(old_ladder.start_date, new_ladder.start_date)
        self.assertEqual(old_ladder.end_date, new_ladder.end_date)
        self.assertEqual(old_ladder.distance_penalty_on, new_ladder.distance_penalty_on)
        self.assertEqual(old_ladder.weeks_for_borrowed_points, new_ladder.weeks_for_borrowed_points)

        # These fields should change
        self.assertEqual(proposed_ladder.weeks_for_borrowed_points_left, new_ladder.weeks_for_borrowed_points_left)

    def test_get_users_ladder_ids(self):
        # Test a user not in any ladders
        self.assertEqual([], self.dao.get_users_ladder_ids("TEST5"))

        # Test a user in ladders
        ladder_ids = self.dao.get_users_ladder_ids("TEST1")
        self.assertTrue(2, len(ladder_ids))
        self.assertTrue(-3 in ladder_ids)
        self.assertTrue(-4 in ladder_ids)

    def test_get_players(self):
        # Test running the SQL, and deserializing a result set
        players = self.dao.get_players(-3)
        self.assertIsNotNone(players)
        self.assertEqual(3, len(players))

        # Test that the order is correct, and that all values were deserialized
        player = players[0]
        self.assertEqual("TEST2", player.user.user_id)
        self.assertEqual("Tester Two", player.user.name)
        self.assertEqual("test2@mail.com", player.user.email)
        self.assertEqual("test2.jpg", player.user.photo_url)
        self.assertEqual(-3, player.ladder_id)
        self.assertEqual(10, player.score)
        self.assertEqual(1, player.ranking)
        self.assertEqual(0, player.wins)
        self.assertEqual(1, player.losses)

        # Test ranking system
        self.assertEqual(1, players[0].ranking)
        self.assertEqual(1, players[1].ranking)
        self.assertEqual(2, players[2].ranking)

    def test_get_players_before_borrowed_points_should_sort_by_order(self):
        players = self.dao.get_players(-4)
        self.assertIsNotNone(players)
        self.assertEqual(2, len(players))
        self.assertEqual("TEST4", players[0].user.user_id)
        self.assertEqual("TEST1", players[1].user.user_id)

    def test_get_player(self):
        # Test a non-existent player
        player = self.dao.get_player(-3, "TEST0")
        self.assertIsNone(player)

        # Test regular player
        player = self.dao.get_player(-3, "TEST1")
        self.assertIsNotNone(player)

    def test_create_player(self):
        self.dao.create_player(-4, "TEST2")
        score = self.dao.get_one(int, "select SCORE from players_vw where LADDER_ID = -4 and USER_ID = 'TEST2'")
        self.assertEqual(0, score)

    def test_update_player_order_empty_should_do_nothing(self):
        original_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", original_players[0].user.user_id)
        self.assertEqual("TEST1", original_players[1].user.user_id)
        self.dao.update_player_order(-4, [])
        new_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", new_players[0].user.user_id)
        self.assertEqual("TEST1", new_players[1].user.user_id)

    def test_update_player_order_with_all_players_should_affect_sorting(self):
        original_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", original_players[0].user.user_id)
        self.assertEqual("TEST1", original_players[1].user.user_id)
        self.dao.update_player_order(-4, [["TEST1", 2], ["TEST4", 1]])
        new_players = self.dao.get_players(-4)
        self.assertEqual("TEST1", new_players[0].user.user_id)
        self.assertEqual("TEST4", new_players[1].user.user_id)

    def test_update_player_order_with_partial_players_should_put_excluded_players_at_the_bottom(self):
        original_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", original_players[0].user.user_id)
        self.assertEqual("TEST1", original_players[1].user.user_id)
        self.dao.update_player_order(-4, [["TEST1", 1]])
        new_players = self.dao.get_players(-4)
        self.assertEqual("TEST1", new_players[0].user.user_id)
        self.assertEqual("TEST4", new_players[1].user.user_id)

    def test_update_all_borrowed_points_empty_should_do_nothing(self):
        original_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", original_players[0].user.user_id)
        self.assertEqual("TEST1", original_players[1].user.user_id)
        self.dao.update_all_borrowed_points(-4, [])
        new_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", new_players[0].user.user_id)
        self.assertEqual(0, new_players[0].borrowed_points)
        self.assertEqual("TEST1", new_players[1].user.user_id)
        self.assertEqual(0, new_players[1].borrowed_points)

    def test_update_all_borrowed_points_with_all_players_should_affect_sorting(self):
        original_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", original_players[0].user.user_id)
        self.assertEqual("TEST1", original_players[1].user.user_id)
        self.dao.update_all_borrowed_points(-4, [["TEST4", 24], ["TEST1", 48]])
        new_players = self.dao.get_players(-4)
        self.assertEqual("TEST1", new_players[0].user.user_id)
        self.assertEqual(48, new_players[0].borrowed_points)
        self.assertEqual("TEST4", new_players[1].user.user_id)
        self.assertEqual(24, new_players[1].borrowed_points)

    def test_update_all_borrowed_points_with_partial_players_should_put_excluded_players_at_the_bottom(self):
        original_players = self.dao.get_players(-4)
        self.assertEqual("TEST4", original_players[0].user.user_id)
        self.assertEqual("TEST1", original_players[1].user.user_id)
        self.dao.update_all_borrowed_points(-4, [["TEST1", 1]])
        new_players = self.dao.get_players(-4)
        self.assertEqual("TEST1", new_players[0].user.user_id)
        self.assertEqual(1, new_players[0].borrowed_points)
        self.assertEqual("TEST4", new_players[1].user.user_id)
        self.assertEqual(0, new_players[1].borrowed_points)

    def test_decrement_borrowed_points(self):
        players = self.dao.get_players(-5)
        self.assertEqual(30, players[0].borrowed_points)

        self.dao.decrement_borrowed_points(-5, 6, 5)
        players = self.dao.get_players(-5)
        self.assertEqual(25, players[0].borrowed_points)

        self.dao.decrement_borrowed_points(-5, 5, 3)
        players = self.dao.get_players(-5)
        self.assertEqual(15, players[0].borrowed_points)

    def test_update_borrowed_points(self):
        get_score_sql = "select SCORE from players_vw where USER_ID = 'TEST1' and LADDER_ID = -4"

        # Make sure the user starts out with no points
        self.assertEqual(0, self.dao.get_one(int, get_score_sql))
        self.dao.update_borrowed_points(-4, "TEST1", 100)
        self.assertEqual(100, self.dao.get_one(int, get_score_sql))

        # Reset the score back to 0
        self.dao.execute("update players set BORROWED_POINTS = 0 where USER_ID = 'TEST1' and LADDER_ID = -4")

    def test_update_earned_points(self):
        get_score_sql = "select SCORE from players_vw where USER_ID = 'TEST1' and LADDER_ID = -4"

        # Make sure the user starts out with no points
        self.assertEqual(0, self.dao.get_one(int, get_score_sql))
        self.dao.update_earned_points(-4, "TEST1", 100)
        self.assertEqual(100, self.dao.get_one(int, get_score_sql))

        # Test updating someone who already has points (to make sure it adds to what is already there)
        self.dao.update_earned_points(-4, "TEST1", 2)
        self.assertEqual(102, self.dao.get_one(int, get_score_sql))

        # Reset the score back to 0
        self.dao.execute("update players set EARNED_POINTS = 0 where USER_ID = 'TEST1' and LADDER_ID = -4")

    def test_get_matches(self):
        # Test a non-existent ladder
        matches = self.dao.get_matches(-5)
        self.assertEqual(0, len(matches))

        # Test a valid ladder, but a non-existent user
        matches = self.dao.get_matches(-3, "TEST0")
        self.assertEqual(0, len(matches))

        # Test searching without a player
        matches = self.dao.get_matches(-3)
        self.assertEqual(1, len(matches))

        # Test searching for a winner
        matches = self.dao.get_matches(-3, "TEST1")
        self.assertEqual(1, len(matches))

        # Test searching for a loser
        matches = self.dao.get_matches(-3, "TEST2")
        self.assertEqual(1, len(matches))

        # Make sure that winner/loser points are returned
        matches = self.dao.get_matches(-3)
        self.assertEqual(1, len(matches))
        self.assertEqual(28, matches[0].winner_points)
        self.assertEqual(11, matches[0].loser_points)

    def test_get_match(self):
        match = self.dao.get_match(-1)
        self.assertEqual(-3, match.ladder_id)
        self.assertEqual(datetime(2018, 1, 2, 3, 4, 5, tzinfo=mountain_tz), match.match_date)
        self.assertEqual('TEST1', match.winner_id)
        self.assertEqual('TEST2', match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(0, match.loser_set1_score)
        self.assertEqual(0, match.winner_set2_score)
        self.assertEqual(6, match.loser_set2_score)
        self.assertEqual(7, match.winner_set3_score)
        self.assertEqual(5, match.loser_set3_score)
        self.assertEqual(28, match.winner_points)
        self.assertEqual(11, match.loser_points)

    def test_create_match(self):
        # Test with null values
        match = self.dao.create_match(Match(None, -3, datetime(2018, 1, 1, 1, 0, 0), "TEST1", "TEST2", 6, 1, 6, 2))
        self.assertEqual(-3, match.ladder_id)
        self.assertEqual(datetime(2018, 1, 1, 1, 0, 0, tzinfo=mountain_tz), match.match_date)
        self.assertEqual("TEST1", match.winner_id)
        self.assertEqual("TEST2", match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(1, match.loser_set1_score)
        self.assertEqual(6, match.winner_set2_score)
        self.assertEqual(2, match.loser_set2_score)
        self.assertIsNone(match.winner_set3_score)
        self.assertIsNone(match.loser_set3_score)

        # Test with a third set
        match = self.dao.create_match(Match(None, -3, datetime(2018, 1, 1, 1, 0, 0), "TEST3", "TEST4", 6, 1, 2, 6, 7, 5))
        self.assertEqual(-3, match.ladder_id)
        self.assertEqual(datetime(2018, 1, 1, 1, 0, 0, tzinfo=mountain_tz), match.match_date)
        self.assertEqual("TEST3", match.winner_id)
        self.assertEqual("TEST4", match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(1, match.loser_set1_score)
        self.assertEqual(2, match.winner_set2_score)
        self.assertEqual(6, match.loser_set2_score)
        self.assertEqual(7, match.winner_set3_score)
        self.assertEqual(5, match.loser_set3_score)

    def test_update_match_score(self):
        sql = "select ID, LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE, WINNER_POINTS, LOSER_POINTS from matches where ID = -1"
        new_match = Match(-1, -4, datetime(2020, 2, 3, 4, 5, 6), 'TEST2', 'TEST1', 3, 4, 5, 6, 7, 8, 9, 10)

        self.dao.update_match(new_match)
        saved_match = self.dao.get_one(Match, sql)
        self.assertEqual(-4, saved_match.ladder_id)
        self.assertEqual(datetime(2020, 2, 3, 4, 5, 6, tzinfo=mountain_tz), saved_match.match_date)
        self.assertEqual('TEST2', saved_match.winner_id)
        self.assertEqual('TEST1', saved_match.loser_id)
        self.assertEqual(3, saved_match.winner_set1_score)
        self.assertEqual(4, saved_match.loser_set1_score)
        self.assertEqual(5, saved_match.winner_set2_score)
        self.assertEqual(6, saved_match.loser_set2_score)
        self.assertEqual(7, saved_match.winner_set3_score)
        self.assertEqual(8, saved_match.loser_set3_score)
        self.assertEqual(9, saved_match.winner_points)
        self.assertEqual(10, saved_match.loser_points)

    def test_delete_match(self):
        sql = "select ID, LADDER_ID, MATCH_DATE, WINNER_ID, LOSER_ID, WINNER_SET1_SCORE, LOSER_SET1_SCORE, WINNER_SET2_SCORE, LOSER_SET2_SCORE, WINNER_SET3_SCORE, LOSER_SET3_SCORE, WINNER_POINTS, LOSER_POINTS from matches where ID = -2"

        self.dao.delete_match(-1)
        self.assertIsNone(self.dao.get_one(Match, sql))

    def test_get_ladder_code(self):
        # Test ladder with code
        code = self.dao.get_ladder_code(-3)
        self.assertEqual("good", code)
