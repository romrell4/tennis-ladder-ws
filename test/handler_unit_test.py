import unittest
import json
from src import handler
from src.domain import *

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = MockManager()
        cls.handler = handler.Handler(cls.manager)

    def test_login(self):
        response = self.handler.handle({
            "resource": "/users",
            "httpMethod": "POST"
        })
        self.assertEqual(200, response["statusCode"])
        user = json.loads(response["body"])
        self.assertEqual(1, user["user_id"])
        self.assertEqual("User1", user["name"])

    def test_get_ladders(self):
        response = self.handler.handle({
            "resource": "/ladders",
            "httpMethod": "GET"
        })
        self.assertEqual(200, response["statusCode"])
        ladders = json.loads(response["body"])
        self.assertEqual(2, len(ladders))
        self.assertEqual(1, ladders[0]["ladder_id"])
        self.assertEqual("Ladder1", ladders[0]["name"])
        self.assertEqual("2018-01-01", ladders[0]["start_date"])
        self.assertEqual("2018-02-01", ladders[0]["end_date"])

    def test_get_players(self):
        response = self.handler.handle({
            "resource": "/ladders/{ladder_id}/players",
            "httpMethod": "GET",
            "pathParameters": {"ladder_id": "1"}
        })
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(1, len(players))
        self.assertEqual(1, players[0]["user_id"])
        self.assertEqual(1, players[0]["ladder_id"])
        self.assertEqual("User1", players[0]["name"])
        self.assertEqual(10, players[0]["score"])

        response = self.handler.handle({
            "resource": "/ladders/{ladder_id}/players",
            "httpMethod": "GET",
            "pathParameters": {"ladder_id": "2"}
        })
        self.assertEqual(200, response["statusCode"])
        players = json.loads(response["body"])
        self.assertEqual(2, len(players))

    def test_add_player_to_ladder(self):
        response = self.handler.handle({
            "resource": "/ladders/{ladder_id}/players/{user_id}",
            "httpMethod": "POST",
            "pathParameters": {"ladder_id": "1", "user_id": "1"}
        })
        self.assertEqual(200, response["statusCode"])
        player = json.loads(response["body"])
        self.assertEqual(1, player["user_id"])
        self.assertEqual(1, player["ladder_id"])
        self.assertEqual("New Player", player["name"])
        self.assertEqual(10, player["score"])

class MockManager():
    def __init__(self):
        self.user = User(1, "User1")

    def login(self):
        return self.user

    def get_ladders(self):
        return [
            Ladder(1, "Ladder1", "2018-01-01", "2018-02-01"),
            Ladder(2, "Ladder2", "2018-02-01", "2018-03-01")
        ]

    def get_players(self, ladder_id):
        if ladder_id == 1:
            return [
                Player(1, 1, "User1", 10)
            ]
        elif ladder_id == 2:
            return [
                Player(2, 2, "User2", 0),
                Player(3, 2, "User3", 0)
            ]

    def add_player_to_ladder(self, ladder_id, user_id):
        return Player(user_id, ladder_id, "New Player", 10)