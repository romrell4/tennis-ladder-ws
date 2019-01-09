import unittest
from datetime import datetime
import copy

from bl import Manager
from domain import ServiceException, Ladder, Player, Match, User

class Test(unittest.TestCase):
    def setUp(self):
        self.manager = Manager(MockFirebaseClient(), MockDao())

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
        self.assertEqual(None, self.manager.user.phone_number)
        self.assertEqual("PICTURE", self.manager.user.photo_url)

        # Test a saved user
        self.manager.firebase_client.valid_user = True
        self.manager.validate_token("")
        self.assertIsNotNone(self.manager.user)
        self.assertFalse(self.manager.dao.created_user)

    def test_add_player_to_ladder(self):
        def assert_error(ladder_id, code, status_code, error_message):
            with self.assertRaises(ServiceException) as e:
                self.manager.add_player_to_ladder(ladder_id, code)
            self.assertEqual(status_code, e.exception.status_code)
            self.assertEqual(error_message, e.exception.error_message)

        # Test when not logged in
        assert_error(None, None, 401, "Unable to authenticate")
        self.manager.user = User("USER1", "User", "user@test.com", None, "user.jpg")

        # Test with null ladder_id
        assert_error(None, None, 400, "Null ladder_id param")

        # Test with a non existent ladder
        assert_error(0, None, 404, "No ladder with id: '0'")

        # Test with no code (when there is supposed to be one)
        assert_error(1, None, 400, "The code provided does not match the code of the ladder. If you believe this in error, please contact the ladder's sponsor.")

        # Test with a a bad code
        assert_error(1, "bad", 400, "The code provided does not match the code of the ladder. If you believe this in error, please contact the ladder's sponsor.")

        # Test valid code
        players = self.manager.add_player_to_ladder(1, "good")
        self.assertIsNotNone(players)

        # Test a ladder without a code
        players = self.manager.add_player_to_ladder(2, None)
        self.assertIsNotNone(players)

        # Test passing in a code, even when there is no code
        players = self.manager.add_player_to_ladder(2, "bad")
        self.assertIsNotNone(players)

        # Remove the user
        self.manager.user = None

    def test_get_matches(self):
        matches = self.manager.get_matches(1, "TEST1")
        self.assertIsNotNone(matches)
        self.assertEqual(1, len(matches))
        self.assertEqual(1, matches[0].match_id)
        self.assertEqual("TEST1", matches[0].winner.user.user_id)
        self.assertEqual("Player 1", matches[0].winner.user.name)
        self.assertEqual("TEST2", matches[0].loser.user.user_id)
        self.assertEqual("Player 2", matches[0].loser.user.name)

    def test_report_match(self):
        def assert_error(ladder_id, match_dict, status_code, error_message):
            with self.assertRaises(ServiceException) as e:
                self.manager.report_match(ladder_id, match_dict)
            self.assertEqual(status_code, e.exception.status_code)
            self.assertEqual(error_message, e.exception.error_message)

        def create_match(winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score = None, loser_set3_score = None):
            return {
                "ladder_id": 1,
                "match_date": None,
                "winner": {
                    "user": {
                        "user_id": winner_id
                    }
                },
                "loser": {
                    "user": {
                        "user_id": loser_id
                    }
                },
                "winner_set1_score": winner_set1_score,
                "loser_set1_score": loser_set1_score,
                "winner_set2_score": winner_set2_score,
                "loser_set2_score": loser_set2_score,
                "winner_set3_score": winner_set3_score,
                "loser_set3_score": loser_set3_score
            }

        # Overwrite the calculate scores function for easier testing
        old_calculate_scores = Match.calculate_scores
        old_validate = Match.validate
        Match.calculate_scores = lambda _, x, y: (10, 5)
        Match.validate = lambda match: match

        # Test when the manager doesn't have a user
        assert_error(0, {}, 401, "Unable to authenticate")
        self.manager.user = User("USER1", "User", "user@test.com", None, "user.jpg")

        # Test with a null ladder_id
        assert_error(None, None, 400, "Null ladder_id param")

        # Test with a null match
        assert_error(0, None, 400, "Null match param")

        # Test with a non-existent ladder
        assert_error(0, {}, 404, "No ladder with id: '0'")

        # Test with a winner/loser not in the specified ladder
        assert_error(1, create_match("TEST0", "TEST1", 6, 0, 6, 0), 400, "No user with id: 'TEST0'")
        assert_error(1, create_match("TEST1", "TEST0", 6, 0, 6, 0), 400, "No user with id: 'TEST0'")

        # Test with a match where players are too far apart
        assert_error(1, create_match("TEST1", "TEST14", 6, 0, 6, 0), 400, "Players are too far apart in the rankings to challenge one another")

        # Test valid match (scores should get updated, and match should be saved with a new date value)
        match = self.manager.report_match(1, create_match("TEST1", "TEST2", 6, 0, 6, 0))
        self.assertEqual(2, len(self.manager.dao.updated_scores))
        self.assertEqual(10, self.manager.dao.updated_scores[0][2])
        self.assertEqual(5, self.manager.dao.updated_scores[1][2])
        self.assertIsNotNone(match.match_id)
        self.assertIsNotNone(self.manager.dao.saved_match)
        self.assertIsNotNone(self.manager.dao.saved_match.match_date)
        self.assertIsNotNone(match)

        # Set mocked function back to originals
        Match.calculate_scores = old_calculate_scores
        Match.validate = old_validate
        self.manager.user = None

class MockFirebaseClient:
    valid_user = True

    def get_firebase_user(self, token):
        if self.valid_user:
            return {"user_id": "USER_ID", "name": "NAME", "email": "EMAIL", "picture": "PICTURE"}
        else:
            return {}

class MockDao:
    user_database = {}
    ladder_database = {
        1: Ladder(1, "Ladder 1", "2018-01-01", "2018-01-02", False),
        2: Ladder(2, "Ladder 2", "2018-01-01", "2018-01-02", False)
    }
    players_database = {
        "TEST1": Player("TEST1", "Player 1", "test1@mail.com", "000-000-0001", "test1.jpg", 1, 100, 1, 0, 0),
        "TEST2": Player("TEST2", "Player 2", "test2@mail.com", "000-000-0002", "test2.jpg", 1, 95, 2, 0, 0),
        "TEST3": Player("TEST3", "Player 3", "test3@mail.com", "000-000-0003", "test3.jpg", 1, 90, 3, 0, 0),
        "TEST4": Player("TEST4", "Player 4", "test4@mail.com", "000-000-0004", "test4.jpg", 1, 85, 4, 0, 0),
        "TEST5": Player("TEST5", "Player 5", "test5@mail.com", "000-000-0005", "test5.jpg", 1, 80, 5, 0, 0),
        "TEST6": Player("TEST6", "Player 6", "test6@mail.com", "000-000-0006", "test6.jpg", 1, 75, 6, 0, 0),
        "TEST7": Player("TEST7", "Player 7", "test7@mail.com", "000-000-0007", "test7.jpg", 1, 70, 7, 0, 0),
        "TEST8": Player("TEST8", "Player 8", "test8@mail.com", "000-000-0008", "test8.jpg", 1, 65, 8, 0, 0),
        "TEST9": Player("TEST9", "Player 9", "test9@mail.com", "000-000-0009", "test9.jpg", 1, 60, 9, 0, 0),
        "TEST10": Player("TEST10", "Player 10", "test10@mail.com", "000-000-0010", "test10.jpg", 1, 55, 10, 0, 0),
        "TEST11": Player("TEST11", "Player 11", "test11@mail.com", "000-000-0011", "test11.jpg", 1, 50, 11, 0, 0),
        "TEST12": Player("TEST12", "Player 12", "test12@mail.com", "000-000-0012", "test12.jpg", 1, 45, 12, 0, 0),
        "TEST13": Player("TEST13", "Player 13", "test13@mail.com", "000-000-0013", "test13.jpg", 1, 40, 13, 0, 0),
        "TEST14": Player("TEST14", "Player 14", "test14@mail.com", "000-000-0014", "test14.jpg", 1, 35, 14, 0, 0),
        "TEST15": Player("TEST15", "Player 15", "test15@mail.com", "000-000-0015", "test15.jpg", 1, 30, 15, 0, 0),
        "TEST16": Player("TEST16", "Player 16", "test16@mail.com", "000-000-0016", "test16.jpg", 1, 25, 16, 0, 0),
        "TEST17": Player("TEST17", "Player 17", "test17@mail.com", "000-000-0017", "test17.jpg", 1, 20, 17, 0, 0),
        "TEST18": Player("TEST18", "Player 18", "test18@mail.com", "000-000-0018", "test18.jpg", 1, 15, 18, 0, 0),
        "TEST19": Player("TEST19", "Player 19", "test19@mail.com", "000-000-0019", "test19.jpg", 1, 10, 19, 0, 0),
        "TEST20": Player("TEST20", "Player 20", "test20@mail.com", "000-000-0020", "test20.jpg", 1, 5, 20, 0, 0)
    }
    updated_scores = []
    saved_match = None
    created_user = False

    def get_user(self, user_id):
        self.created_user = False
        return self.user_database.get(user_id)

    def create_user(self, user):
        self.user_database[user.user_id] = user
        self.created_user = True
        return user

    def get_ladders(self):
        return self.ladder_database.values()

    def get_ladder(self, ladder_id):
        return self.ladder_database.get(ladder_id)

    def get_players(self, ladder_id):
        return [player for player in self.players_database.values() if player.ladder_id == ladder_id]

    def get_player(self, ladder_id, user_id):
        return self.players_database.get(user_id)

    def create_player(self, ladder_id, user_id):
        pass

    def update_score(self, user_id, ladder_id, new_score_to_add):
        self.updated_scores.append([user_id, ladder_id, new_score_to_add])

    def get_matches(self, ladder_id, user_id):
        return [
            Match(1, ladder_id, datetime(2018, 1, 1, 12, 30, 0), "TEST1", "TEST2", 6, 0, 6, 0)
        ]

    def create_match(self, match):
        self.saved_match = match
        new_match = copy.deepcopy(match)
        new_match.match_id = 0
        return new_match

    def get_ladder_code(self, ladder_id):
        return "good" if ladder_id == 1 else None
