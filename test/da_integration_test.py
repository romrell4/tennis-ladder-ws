import unittest
import os
from datetime import datetime

import properties
from da import Dao
from domain import *

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["DB_HOST"] = properties.db_host
        os.environ["DB_USERNAME"] = properties.db_username
        os.environ["DB_PASSWORD"] = properties.db_password
        os.environ["DB_DATABASE_NAME"] = properties.db_database_name

        cls.dao = Dao()
        try:
            cls.dao.insert("INSERT INTO users (ID, NAME, EMAIL, PHOTO_URL) VALUES ('-1', 'Tester One', 'test1@mail.com', 'test1.jpg')")
            cls.dao.insert("INSERT INTO users (ID, NAME, EMAIL, PHOTO_URL) VALUES ('-2', 'Tester Two', 'test2@mail.com', 'test2.jpg')")
            cls.dao.insert("INSERT INTO ladders (ID, NAME, START_DATE, END_DATE) VALUES ('-3', 'Test 1', DATE '2018-01-01', DATE '2018-01-02')")
            cls.dao.insert("INSERT INTO ladders (ID, NAME, START_DATE, END_DATE) VALUES ('-4', 'Test 2', DATE '2018-02-01', DATE '2018-02-02')")
            cls.dao.insert("INSERT INTO scores (USER_ID, LADDER_ID, SCORE) VALUES ('-1', -3, 5)")
            cls.dao.insert("INSERT INTO scores (USER_ID, LADDER_ID, SCORE) VALUES ('-2', -3, 10)")
            cls.dao.insert("INSERT INTO scores (USER_ID, LADDER_ID, SCORE) VALUES ('-1', -4, 0)")
        except:
            cls.tearDownClass()
            exit()

    @classmethod
    def tearDownClass(cls):
        # These will cascade in order to delete the other ones
        cls.dao.execute("DELETE FROM users where ID in ('-1', '-2')")
        cls.dao.execute("DELETE FROM ladders where ID in ('-3', '-4')")

    def test_get_user(self):
        # Test non-existent user
        user = self.dao.get_user("0")
        self.assertIsNone(user)

        # Test regular user
        user = self.dao.get_user("-1")
        self.assertIsNotNone(user)
        self.assertEqual("-1", user.user_id)
        self.assertEqual("Tester One", user.name)
        self.assertEqual("test1@mail.com", user.email)
        self.assertEqual("test1.jpg", user.photo_url)

    def test_create_user(self):
        try:
            self.dao.create_user(User("__TEST", "Tester", "test@test.com", "test.jpg"))
            user = self.dao.get_one(User, "SELECT * FROM users where ID = '__TEST'")
            self.assertIsNotNone(user)
            self.assertEqual("__TEST", user.user_id)
            self.assertEqual("Tester", user.name)
            self.assertEqual("test@test.com", user.email)
            self.assertEqual("test.jpg", user.photo_url)
        finally:
            self.dao.execute("DELETE FROM users where ID = '__TEST'")

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
        self.assertEqual("2018-02-01", ladder.start_date)
        self.assertEqual("2018-02-02", ladder.end_date)

    def test_get_players(self):
        # Test running the SQL, and deserializing a result set
        players = self.dao.get_players(-3)
        self.assertIsNotNone(players)
        self.assertEqual(2, len(players))

        # Test that the order is correct
        player = players[0]
        self.assertEqual("-2", player.user_id)
        self.assertEqual(-3, player.ladder_id)
        self.assertEqual(10, player.score)

    def test_create_match(self):
        # Test with null values
        match = self.dao.create_match(Match(None, -3, datetime(2018, 1, 1, 1, 0, 0), -1, -2, 6, 1, 6, 2, None, None))
        self.assertEqual(-3, match.ladder_id)
        self.assertEqual(datetime(2018, 1, 1, 1, 0, 0), match.match_date)
        self.assertEqual("-1", match.winner_id)
        self.assertEqual("-2", match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(1, match.loser_set1_score)
        self.assertEqual(6, match.winner_set2_score)
        self.assertEqual(2, match.loser_set2_score)
        self.assertIsNone(match.winner_set3_score)
        self.assertIsNone(match.loser_set3_score)

        # Test with a third set
        match = self.dao.create_match(Match(None, -3, datetime(2018, 1, 1, 1, 0, 0), -1, -2, 6, 1, 2, 6, 7, 5))
        self.assertEqual(-3, match.ladder_id)
        self.assertEqual(datetime(2018, 1, 1, 1, 0, 0), match.match_date)
        self.assertEqual("-1", match.winner_id)
        self.assertEqual("-2", match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(1, match.loser_set1_score)
        self.assertEqual(2, match.winner_set2_score)
        self.assertEqual(6, match.loser_set2_score)
        self.assertEqual(7, match.winner_set3_score)
        self.assertEqual(5, match.loser_set3_score)

    def test_update_score(self):
        self.dao.update_score(-1, -4, 100)
        self.assertEqual(100, self.dao.get_one(Score, "SELECT * FROM scores WHERE USER_ID = %s and LADDER_ID = %s", -1, -4).score)
