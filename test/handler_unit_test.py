import unittest
import json
from src import handler
from src.domain import *
from datetime import datetime, date

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = MockManager()
        cls.handler = handler.Handler(cls.manager)

    def test_get_ladders(self):
        response = self.handler.handle(create_event("/ladders"))
        self.assertEqual(200, response["statusCode"])
        ladders = json.loads(response["body"])
        self.assertEqual(2, len(ladders))
        self.assertEqual(1, ladders[0]["ladder_id"])
        self.assertEqual("Ladder1", ladders[0]["name"])
        self.assertEqual("2018-01-01", ladders[0]["start_date"])
        self.assertEqual("2018-02-01", ladders[0]["end_date"])

    def test_get_players(self):
        # Test a ladder with a single player
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(1, len(players))
        self.assertEqual(1, players[0]["user_id"])
        self.assertEqual(1, players[0]["ladder_id"])
        self.assertEqual("User1", players[0]["name"])
        self.assertEqual(10, players[0]["score"])
        self.assertEqual(3, players[0]["ranking"])
        self.assertEqual(1, players[0]["wins"])
        self.assertEqual(0, players[0]["losses"])

        # Test a ladder with multiple players
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "2"}))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(2, len(players))

    def test_get_matches(self):
        # Test a user who's played in a single match in a ladder
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players/{user_id}/matches", {"ladder_id": "1", "user_id": "1"}))
        self.assertEqual(200, response["statusCode"])
        matches = json.loads(response["body"])
        self.assertEqual(1, len(matches))
        self.assertEqual(1, matches[0]["match_id"])
        self.assertEqual(1, matches[0]["ladder_id"])
        self.assertEqual("2018-01-01T01:00:00", matches[0]["match_date"])
        self.assertEqual(1, matches[0]["winner_id"])
        self.assertEqual(2, matches[0]["loser_id"])
        self.assertEqual(6, matches[0]["winner_set1_score"])
        self.assertEqual(0, matches[0]["loser_set1_score"])
        self.assertEqual(0, matches[0]["winner_set2_score"])
        self.assertEqual(6, matches[0]["loser_set2_score"])
        self.assertEqual(7, matches[0]["winner_set3_score"])
        self.assertEqual(5, matches[0]["loser_set3_score"])

        # Test a user who's played in multiple matches in a ladder
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players/{user_id}/matches", {"ladder_id": "2", "user_id": "1"}))
        self.assertEqual(200, response["statusCode"])
        matches = json.loads(response["body"])
        self.assertEqual(2, len(matches))

    def test_report_match(self):
        response = self.handler.handle(create_event("/ladders/{ladder_id}/matches", {"ladder_id": "1"}, "POST", "{}"))
        self.assertEqual(200, response["statusCode"])
        match = json.loads(response["body"])
        self.assertEqual(1, match["match_id"])
        self.assertEqual(1, match["ladder_id"])
        self.assertEqual("2018-02-02T01:00:00", match["match_date"])
        self.assertEqual(2, match["winner_id"])
        self.assertEqual(3, match["loser_id"])
        self.assertEqual(6, match["winner_set1_score"])
        self.assertEqual(0, match["loser_set1_score"])
        self.assertEqual(5, match["winner_set2_score"])
        self.assertEqual(7, match["loser_set2_score"])
        self.assertEqual(6, match["winner_set3_score"])
        self.assertEqual(3, match["loser_set3_score"])

    def test_get_token(self):
        response = self.handler.get_token({
            "headers": {"X-Firebase-Token": "TEST"}
        })
        self.assertEqual("TEST", response)

def create_event(resource, path_params = {}, method = "GET", body = None):
    return {
        "resource": resource,
        "pathParameters": path_params,
        "httpMethod": method,
        "headers": {"X-Firebase-Token": ""}
    }

class MockManager():
    def __init__(self):
        self.user = User("1", "User1", "user@test.com", "hello.jpg")

    def validate_token(self, token):
        pass

    def get_ladders(self):
        return [
            Ladder(1, "Ladder1", date(2018, 1, 1), date(2018, 2, 1)),
            Ladder(2, "Ladder2", date(2018, 2, 1), date(2018, 3, 1))
        ]

    def get_players(self, ladder_id):
        if ladder_id == 1:
            return [
                Player(1, 1, "User1", 10, 3, 1, 0)
            ]
        elif ladder_id == 2:
            return [
                Player(2, 2, "User2", 0, 1, 0, 0),
                Player(3, 2, "User3", 0, 1, 0, 0)
            ]

    def get_matches(self, ladder_id, user_id):
        if ladder_id == 1:
            return [
                Match(1, 1, datetime(2018, 1, 1, 1, 0, 0), 1, 2, 6, 0, 0, 6, 7, 5)
            ]
        elif ladder_id == 2:
            return [
                Match(1, 1, datetime(2018, 1, 1, 1, 0, 0), 1, 2, 6, 0, 6, 0),
                Match(1, 1, datetime(2018, 1, 1, 1, 0, 0), 1, 2, 6, 0, 0, 6, 7, 5)
            ]

    def report_match(self, ladder_id, match):
        return Match(1, 1, datetime(2018, 2, 2, 1, 0, 0), 2, 3, 6, 0, 5, 7, 6, 3)
