import unittest

from bl import Manager
from domain import ServiceException, Ladder

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dao = MockDao()
        cls.manager = Manager(cls.dao)

    def test_login(self):
        pass

    def test_get_ladders(self):
        pass

    def test_get_players(self):
        pass

    def test_report_match(self):
        pass

class MockDao:
    def get_ladders(self):
        pass

    def get_players(self, ladder_id):
        pass

    def create_match(self, match):
        pass

    def update_score(self, user_id, ladder_id, new_score):
        pass
