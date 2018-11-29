import unittest
from src import handler
from src.domain import *

class Test(unittest.TestCase):
    def __init__(self):
        super().__init__()
        manager = MockManager()
        self.handler = handler.Handler(manager)

    def test_handle(self):
        self.handler.handle({

        })

class MockManager():
    def __init__(self):
        self.user = User([0, "Test User"])

    def login(self):
        return self.user

    def get_ladders(self):
        return [
            Ladder([0, "Test Ladder", "2018-01-01", "2018-02-01"]),
            Ladder([0, "Test Ladder", "2018-01-01", "2018-02-01"])
        ]

    def get_players(self, ladder_id):
        return [
            Player()
        ]

    def add_player_to_ladder(self, ladder_id, user_id):
        pass