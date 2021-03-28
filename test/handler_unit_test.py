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

    def test_get_user(self):
        response = self.handler.handle(create_event("/users/{user_id}", {"user_id": "abc"}))
        self.assertEqual(200, response["statusCode"])
        user = json.loads(response["body"])
        self.assertEqual("1", user["user_id"])
        self.assertEqual("User1", user["name"])
        self.assertEqual("user1@test.com", user["email"])
        self.assertEqual("555-555-5555", user["phone_number"])
        self.assertEqual("hello.jpg", user["photo_url"])
        self.assertEqual("avail", user["availability_text"])

    def test_update_user(self):
        response = self.handler.handle(create_event("/users/{user_id}", {"user_id": "abc"}, "PUT", "{}"))
        self.assertEqual(200, response["statusCode"])
        user = json.loads(response["body"])
        self.assertEqual("1", user["user_id"])
        self.assertEqual("User1", user["name"])
        self.assertEqual("user1@test.com", user["email"])
        self.assertEqual("555-555-5555", user["phone_number"])
        self.assertEqual("hello.jpg", user["photo_url"])
        self.assertEqual("avail", user["availability_text"])

    def test_get_ladders(self):
        response = self.handler.handle(create_event("/ladders"))
        self.assertEqual(200, response["statusCode"])
        ladders = json.loads(response["body"])
        self.assertEqual(2, len(ladders))
        self.assertEqual(1, ladders[0]["ladder_id"])
        self.assertEqual("Ladder1", ladders[0]["name"])
        self.assertEqual("2018-01-01", ladders[0]["start_date"])
        self.assertEqual("2018-02-01", ladders[0]["end_date"])
        self.assertFalse(ladders[0]["distance_penalty_on"])

    def test_get_players(self):
        # Test a ladder with a single player
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(1, len(players))
        self.assertEqual(1, players[0]["user"]["user_id"])
        self.assertEqual("User1", players[0]["user"]["name"])
        self.assertEqual("user1@test.com", players[0]["user"]["email"])
        self.assertEqual("test1.jpg", players[0]["user"]["photo_url"])
        self.assertEqual("avail 1", players[0]["user"]["availability_text"])
        self.assertEqual(1, players[0]["ladder_id"])
        self.assertEqual(10, players[0]["score"])
        self.assertEqual(10, players[0]["earned_points"])
        self.assertEqual(0, players[0]["borrowed_points"])
        self.assertEqual(3, players[0]["ranking"])
        self.assertEqual(1, players[0]["wins"])
        self.assertEqual(0, players[0]["losses"])

        # Test a ladder with multiple players
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "2"}))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(2, len(players))

    def test_create_player(self):
        # Test without required code (make sure it defaults instead of throwing an error)
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}, "POST"))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(0, len(players))

        # Test with code
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}, "POST", query_params = {"code": "good"}))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(1, len(players))

    def test_update_player(self):
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players/{user_id}", {"ladder_id": "1", "user_id": "2"}, "PUT", {"borrowed_points": "50"}))
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(1, len(players))

    def test_get_matches(self):
        # Test a user who's played in a single match in a ladder
        response = self.handler.handle(create_event("/ladders/{ladder_id}/players/{user_id}/matches", {"ladder_id": "1", "user_id": "TEST1"}))
        self.assertEqual(200, response["statusCode"])
        matches = json.loads(response["body"])
        self.assertEqual(1, len(matches))
        self.assertEqual(1, matches[0]["match_id"])
        self.assertEqual(1, matches[0]["ladder_id"])
        self.assertEqual("2018-01-01T01:00:00Z", matches[0]["match_date"])
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
        # Valid test
        response = self.handler.handle(create_event("/ladders/{ladder_id}/matches", {"ladder_id": "1"}, "POST", "{}"))
        self.assertEqual(200, response["statusCode"])
        self.assertIsNotNone(MockManager.reported_match)
        MockManager.reported_match = None
        match = json.loads(response["body"])
        self.assertEqual(1, match["match_id"])
        self.assertEqual(1, match["ladder_id"])
        self.assertEqual("2018-02-02T01:00:00Z", match["match_date"])
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

def create_event(resource, path_params = None, method = "GET", body = None, query_params = None):
    event = {
        "resource": resource,
        "httpMethod": method,
        "headers": {"X-Firebase-Token": ""}
    }
    if path_params is not None:
        event["pathParameters"] = path_params
    if body is not None:
        event["body"] = body
    if query_params is not None:
        event["queryStringParameters"] = query_params
    return event

class MockManager():
    reported_match = None

    def __init__(self):
        self.user = User("1", "User1", "user1@test.com", "555-555-5555", "hello.jpg", "avail", False)

    def validate_token(self, token):
        pass

    def get_user(self, user_id):
        return self.user

    def update_user(self, user_id, user):
        return self.user

    def get_ladders(self):
        return [
            Ladder(1, "Ladder1", date(2018, 1, 1), date(2018, 2, 1), False),
            Ladder(2, "Ladder2", date(2018, 2, 1), date(2018, 3, 1), False)
        ]

    def get_players(self, ladder_id):
        if ladder_id == 1:
            return [
                Player(1, "User1", "user1@test.com", "000-000-0000", "test1.jpg", "avail 1", False, 1, 10, 10, 0, 3, 1, 0)
            ]
        elif ladder_id == 2:
            return [
                Player(2, "User2", "user2@test.com", "000-000-0000", "test2.jpg", "avail 2", False, 2, 0, 0, 0, 1, 0, 0),
                Player(3, "User3", "user3@test.com", "000-000-0000", "test3.jpg", "avail 3", False, 2, 0, 0, 0, 1, 0, 0)
            ]

    def add_player_to_ladder(self, ladder_id, code):
        if code is None:
            return []
        else:
            return [
                Player(1, "User1", "user1@test.com", "000-000-0000", "test1.jpg", "avail 1", False, 1, 10, 10, 0, 3, 1, 0)
            ]

    def update_player(self, ladder_id, user_id, player_dict):
        return [
            Player(1, "User1", "user1@test.com", "000-000-0000", "test1.jpg", "avail 1", False, 1, 10, 10, 0, 3, 1, 0)
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
        MockManager.reported_match = match
        return Match(1, 1, datetime(2018, 2, 2, 1, 0, 0), 2, 3, 6, 0, 5, 7, 6, 3)
