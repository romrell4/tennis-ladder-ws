import unittest
from datetime import datetime

from bl import Manager
from domain import ServiceException, Ladder, Player, User

class Test(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manager = Manager(MockFirebaseClient(), MockDao())

    def test_validate_token(self):
        # Test without a token (unauthenticated request)
        self.manager.validate_token(None)
        self.assertIsNone(self.manager.user)

        # Test invalid token response
        self.manager.firebase_client.valid_user = False
        self.manager.validate_token("")
        self.assertIsNone(self.manager.user)

        # Test a new user
        self.manager.firebase_client.valid_user = True
        self.manager.validate_token("")
        self.assertIsNotNone(self.manager.user)
        self.assertTrue(self.manager.dao.created_user)
        self.assertEqual("USER_ID", self.manager.user.user_id)
        self.assertEqual("NAME", self.manager.user.name)
        self.assertEqual("EMAIL", self.manager.user.email)
        self.assertEqual("PICTURE", self.manager.user.photo_url)

        # Test a saved user
        self.manager.firebase_client.valid_user = True
        self.manager.validate_token("")
        self.assertIsNotNone(self.manager.user)
        self.assertFalse(self.manager.dao.created_user)

    def _test_report_match(self):
        def assert_error(ladder_id, match_dict, status_code, error_message):
            with self.assertRaises(ServiceException) as e:
                self.manager.report_match(ladder_id, match_dict)
            self.assertEqual(status_code, e.exception.status_code)
            self.assertEqual(error_message, e.exception.error_message)

        def create_match(winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score = None, loser_set3_score = None):
            return {
                "ladder_id": "1",
                "match_date": datetime(2018, 1, 1, 1, 0, 0),
                "winner_id": winner_id,
                "loser_id": loser_id,
                "winner_set1_score": winner_set1_score,
                "loser_set1_score": loser_set1_score,
                "winner_set2_score": winner_set2_score,
                "loser_set2_score": loser_set2_score,
                "winner_set3_score": winner_set3_score,
                "loser_set3_score": loser_set3_score
            }

        # Test when the manager doesn't have a user
        assert_error(0, {}, 403, "Unable to authenticate")

        # Test with a null ladder_id
        assert_error(None, None, 400, "Null ladder_id param")

        # Test with a null match
        assert_error(0, None, 400, "Null match param")

        # Test with a non-existent ladder
        assert_error(0, {}, 404, "No match with id: '0'")

        # Test with a winner/loser not in the specified ladder
        assert_error(1, create_match(0, 1, 6, 0, 6, 0), 400, "No user with id: '0'")
        assert_error(1, create_match(1, 0, 6, 0, 6, 0), 400, "No user with id: '0'")

        # Test with a match where players are too far apart
        assert_error(1, create_match(1, 14, 6, 0, 6, 0), 400, "Players are too far apart in the rankings to challenge one another")

        # TODO: What other tests are needed? Test most everything else in domain...

class MockFirebaseClient:
    valid_user = True

    def get_firebase_user(self, token):
        if self.valid_user:
            return {"user_id": "USER_ID", "name": "NAME", "email": "EMAIL", "picture": "PICTURE"}
        else:
            return {}

class MockDao:
    user_database = {}
    created_user = False

    def get_user(self, user_id):
        self.created_user = False
        return self.user_database.get(user_id)

    def create_user(self, user):
        self.user_database[user.user_id] = user
        self.created_user = True
        return user

    def get_ladders(self):
        return [
            Ladder(1, "Ladder 1", "2018-01-01", "2018-01-02")
        ]

    def get_players(self, ladder_id):
        return [
            Player(1, ladder_id, "Player 1", 0, 1, 0, 0),
            Player(2, ladder_id, "Player 2", 0, 1, 0, 0),
            Player(3, ladder_id, "Player 3", 0, 1, 0, 0),
            Player(4, ladder_id, "Player 4", 0, 1, 0, 0),
            Player(5, ladder_id, "Player 5", 0, 1, 0, 0),
            Player(6, ladder_id, "Player 6", 0, 1, 0, 0),
            Player(7, ladder_id, "Player 7", 0, 1, 0, 0),
            Player(8, ladder_id, "Player 8", 0, 1, 0, 0),
            Player(9, ladder_id, "Player 9", 0, 1, 0, 0),
            Player(10, ladder_id, "Player 10", 0, 1, 0, 0),
            Player(11, ladder_id, "Player 11", 0, 1, 0, 0),
            Player(12, ladder_id, "Player 12", 0, 1, 0, 0),
            Player(13, ladder_id, "Player 13", 0, 1, 0, 0),
            Player(14, ladder_id, "Player 14", 0, 1, 0, 0),
            Player(15, ladder_id, "Player 15", 0, 1, 0, 0),
            Player(16, ladder_id, "Player 16", 0, 1, 0, 0),
            Player(17, ladder_id, "Player 17", 0, 1, 0, 0),
            Player(18, ladder_id, "Player 18", 0, 1, 0, 0),
            Player(19, ladder_id, "Player 19", 0, 1, 0, 0),
            Player(20, ladder_id, "Player 20", 0, 1, 0, 0)
        ]

    def create_match(self, match):
        pass

    def update_score(self, user_id, ladder_id, new_score):
        pass
