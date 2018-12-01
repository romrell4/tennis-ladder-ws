import unittest

from bl import Manager

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dao = MockDao()
        cls.manager = Manager(cls.dao)


class MockDao:
    def get_ladders(self):
        pass

    def get_players(self, ladder_id):
        pass

    def create_match(self, match):
        pass

    def update_score(self, user_id, ladder_id, new_score):
        pass