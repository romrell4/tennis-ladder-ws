import unittest
import os

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

        cls.da = Dao()
        try:
            cls.da.insert("INSERT INTO users (ID, NAME) VALUES (-1, 'Tester One')")
            cls.da.insert("INSERT INTO users (ID, NAME) VALUES (-2, 'Tester Two')")
            cls.da.insert("INSERT INTO ladders (ID, NAME, START_DATE, END_DATE) VALUES (-3, 'Test 1', DATE '2018-01-01', DATE '2018-01-02')")
            cls.da.insert("INSERT INTO ladders (ID, NAME, START_DATE, END_DATE) VALUES (-4, 'Test 2', DATE '2018-02-01', DATE '2018-02-02')")
            cls.da.insert("INSERT INTO scores (USER_ID, LADDER_ID, SCORE) VALUES (-1, -3, 5)")
            cls.da.insert("INSERT INTO scores (USER_ID, LADDER_ID, SCORE) VALUES (-2, -3, 10)")
            cls.da.insert("INSERT INTO scores (USER_ID, LADDER_ID, SCORE) VALUES (-1, -4, 0)")
        except:
            cls.tearDownClass()
            exit()

    @classmethod
    def tearDownClass(cls):
        # These will cascade in order to delete the other ones
        cls.da.execute("DELETE FROM users where ID in (-1, -2)")
        cls.da.execute("DELETE FROM ladders where ID in (-3, -4)")

    def test_get_ladders(self):
        # Test running the SQL and creating the objects
        ladders = self.da.get_ladders()
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
        players = self.da.get_players(-3)
        self.assertIsNotNone(players)
        self.assertEqual(2, len(players))

        # Test that the order is correct
        player = players[0]
        self.assertEqual(-2, player.user_id)
        self.assertEqual(-3, player.ladder_id)
        self.assertEqual(10, player.score)

    def test_create_match(self):
        # Test with null values
        match = self.da.create_match(Match(None, -1, -2, 6, 1, 6, 2, None, None))
        self.assertEqual(-1, match.winner_id)
        self.assertEqual(-2, match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(1, match.loser_set1_score)
        self.assertEqual(6, match.winner_set2_score)
        self.assertEqual(2, match.loser_set2_score)
        self.assertIsNone(match.winner_set3_score)
        self.assertIsNone(match.loser_set3_score)

        # Test with a third set
        match = self.da.create_match(Match(None, -1, -2, 6, 1, 2, 6, 7, 5))
        self.assertEqual(-1, match.winner_id)
        self.assertEqual(-2, match.loser_id)
        self.assertEqual(6, match.winner_set1_score)
        self.assertEqual(1, match.loser_set1_score)
        self.assertEqual(2, match.winner_set2_score)
        self.assertEqual(6, match.loser_set2_score)
        self.assertEqual(7, match.winner_set3_score)
        self.assertEqual(5, match.loser_set3_score)

    def test_update_score(self):
        self.da.update_score(-1, -4, 100)
        self.assertEqual(100, self.da.get_one(Score, "SELECT * FROM scores WHERE USER_ID = %s and LADDER_ID = %s", -1, -4).score)
