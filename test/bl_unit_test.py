import unittest
from datetime import datetime, timedelta
import copy

from bl import Manager
from domain import ServiceException, Ladder, Player, Match, User

class Test(unittest.TestCase):
    test_user = User("USER1", "User", "user@test.com", "555-555-5555", "user.jpg", "availability")
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
        self.assertEqual(None, self.manager.user.availability_text)

        # Test a saved user
        self.manager.firebase_client.valid_user = True
        self.manager.validate_token("")
        self.assertIsNotNone(self.manager.user)
        self.assertFalse(self.manager.dao.created_user)

    def test_get_user(self):
        def assert_error(user_id, status_code, error_message):
            with self.assertRaises(ServiceException) as e:
                self.manager.get_user(user_id)
            self.assertEqual(status_code, e.exception.status_code)
            self.assertEqual(error_message, e.exception.error_message)

        # Test when not logged in
        assert_error(None, 401, "Unable to authenticate")
        self.manager.user = Test.test_user

        # Test with no user id param
        assert_error(None, 400, "No user_id passed in")

        # Test getting another user
        assert_error("BAD_USER", 403, "You are only allowed to access profile information for users who are playing in the same ladder as you")

        # Test getting yourself
        user = self.manager.get_user(Test.test_user.user_id)
        self.assertEqual(user, Test.test_user)

        # Test getting yourself, when you aren't in a ladder
        old_user_id = self.manager.user.user_id
        self.manager.user.user_id = "BAD_USER"
        user = self.manager.get_user("BAD_USER")
        self.assertEqual(user.user_id, "BAD_USER")
        self.manager.user.user_id = old_user_id

        # Test getting another player
        user = self.manager.get_user("TEST1")
        self.assertEqual(user.user_id, "TEST1")

    def test_update_user(self):
        def assert_error(user_id, user, status_code, error_message):
            with self.assertRaises(ServiceException) as e:
                self.manager.update_user(user_id, user)
            self.assertEqual(status_code, e.exception.status_code)
            self.assertEqual(error_message, e.exception.error_message)

        # Test when not logged in
        assert_error(None, None, 401, "Unable to authenticate")
        self.manager.user = Test.test_user

        # Test with no user id param
        assert_error(None, None, 400, "No user_id passed in")

        # Test with no user param
        assert_error("-1", None, 400, "No user passed in to update")

        # Test updating another user
        assert_error("ANOTHER_USER", Test.test_user, 403, "You are only allowed to update your own profile information")

        # Test without specifying phone (shouldn't update)
        saved_user = self.manager.update_user(Test.test_user.user_id, {})
        self.assertIsNotNone(saved_user.phone_number)

        # Test specifying null phone (should update)
        saved_user = self.manager.update_user(Test.test_user.user_id, {"phone_number": None})
        self.assertIsNone(saved_user.phone_number)

        # Test which info can be updated
        saved_user = self.manager.update_user(Test.test_user.user_id, {"user_id": "bad", "name": "new name", "email": "new email", "phone_number": "new phone", "photo_url": "new url", "availability_text": "new availability"})
        self.assertNotEqual("bad", saved_user.user_id)
        self.assertEqual("new name", saved_user.name)
        self.assertEqual("new email", saved_user.email)
        self.assertEqual("new phone", saved_user.phone_number)
        self.assertEqual("new url", saved_user.photo_url)
        self.assertEqual("new availability", saved_user.availability_text)

    def test_add_player_to_ladder(self):
        def assert_error(ladder_id, code, status_code, error_message):
            with self.assertRaises(ServiceException) as e:
                self.manager.add_player_to_ladder(ladder_id, code)
            self.assertEqual(status_code, e.exception.status_code)
            self.assertEqual(error_message, e.exception.error_message)

        # Test when not logged in
        assert_error(None, None, 401, "Unable to authenticate")
        self.manager.user = Test.test_user

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
        Match.calculate_scores = lambda _, x, y, z: (10, 5)
        Match.validate = lambda match: match

        # Test when the manager doesn't have a user
        assert_error(0, {}, 401, "Unable to authenticate")
        self.manager.user = Test.test_user

        # Test with a null ladder_id
        assert_error(None, None, 400, "Null ladder_id param")

        # Test with a null match
        assert_error(0, None, 400, "Null match param")

        # Test with a non-existent ladder
        assert_error(0, {}, 404, "No ladder with id: '0'")

        # Test reporting a match before the ladder is open
        assert_error(3, create_match("TEST0", "TEST0", 0, 0, 0, 0), 400, "This ladder is not open yet")

        # Test reporting a match after the ladder is closed
        assert_error(4, create_match("TEST0", "TEST0", 0, 0, 0, 0), 400, "This ladder is now closed")

        # Test with a winner/loser not in the specified ladder
        assert_error(1, create_match("TEST0", "TEST1", 6, 0, 6, 0), 400, "No user with id: 'TEST0'")
        assert_error(1, create_match("TEST1", "TEST0", 6, 0, 6, 0), 400, "No user with id: 'TEST0'")

        # Test with a match where players are too far apart (should work if distance penalty is off)
        self.manager.report_match(1, create_match("TEST1", "TEST14", 6, 0, 6, 0))
        assert_error(2, create_match("TEST1", "TEST14", 6, 0, 6, 0), 400, "Players are too far apart in the rankings to challenge one another")

        # Test valid match (scores should get updated, and match should be saved with a new date value)
        self.manager.dao.updated_scores = []
        self.manager.dao.saved_match = None
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

def create_date(day_offset):
    return datetime.today() + timedelta(days = day_offset)

class MockDao:
    user_database = {
        Test.test_user.user_id: Test.test_user,
        "TEST1": User("TEST1", None, None, None, None, None),
        "BAD_USER": User("BAD_USER", None, None, None, None, None)
    }
    ladder_database = {
        1: Ladder(1, "Ladder 1", create_date(-1), create_date(1), False),
        2: Ladder(2, "Ladder 2", create_date(-1), create_date(1), True),
        3: Ladder(3, "Ladder 3", create_date(1), create_date(2), False),
        4: Ladder(4, "Ladder 4", create_date(-2), create_date(-1), False)
    }
    players_database = {
        "TEST1": Player("TEST1", "Player 1", "test1@mail.com", "000-000-0001", "test1.jpg", "availability 1", 1, 100, 1, 0, 0),
        "TEST2": Player("TEST2", "Player 2", "test2@mail.com", "000-000-0002", "test2.jpg", "availability 2", 1, 95, 2, 0, 0),
        "TEST3": Player("TEST3", "Player 3", "test3@mail.com", "000-000-0003", "test3.jpg", "availability 3", 1, 90, 3, 0, 0),
        "TEST4": Player("TEST4", "Player 4", "test4@mail.com", "000-000-0004", "test4.jpg", "availability 4", 1, 85, 4, 0, 0),
        "TEST5": Player("TEST5", "Player 5", "test5@mail.com", "000-000-0005", "test5.jpg", "availability 5", 1, 80, 5, 0, 0),
        "TEST6": Player("TEST6", "Player 6", "test6@mail.com", "000-000-0006", "test6.jpg", "availability 6", 1, 75, 6, 0, 0),
        "TEST7": Player("TEST7", "Player 7", "test7@mail.com", "000-000-0007", "test7.jpg", "availability 7", 1, 70, 7, 0, 0),
        "TEST8": Player("TEST8", "Player 8", "test8@mail.com", "000-000-0008", "test8.jpg", "availability 8", 1, 65, 8, 0, 0),
        "TEST9": Player("TEST9", "Player 9", "test9@mail.com", "000-000-0009", "test9.jpg", "availability 9", 1, 60, 9, 0, 0),
        "TEST10": Player("TEST10", "Player 10", "test10@mail.com", "000-000-0010", "test10.jpg", "availability 10", 1, 55, 10, 0, 0),
        "TEST11": Player("TEST11", "Player 11", "test11@mail.com", "000-000-0011", "test11.jpg", "availability 11", 1, 50, 11, 0, 0),
        "TEST12": Player("TEST12", "Player 12", "test12@mail.com", "000-000-0012", "test12.jpg", "availability 12", 1, 45, 12, 0, 0),
        "TEST13": Player("TEST13", "Player 13", "test13@mail.com", "000-000-0013", "test13.jpg", "availability 13", 1, 40, 13, 0, 0),
        "TEST14": Player("TEST14", "Player 14", "test14@mail.com", "000-000-0014", "test14.jpg", "availability 14", 1, 35, 14, 0, 0),
        "TEST15": Player("TEST15", "Player 15", "test15@mail.com", "000-000-0015", "test15.jpg", "availability 15", 1, 30, 15, 0, 0),
        "TEST16": Player("TEST16", "Player 16", "test16@mail.com", "000-000-0016", "test16.jpg", "availability 16", 1, 25, 16, 0, 0),
        "TEST17": Player("TEST17", "Player 17", "test17@mail.com", "000-000-0017", "test17.jpg", "availability 17", 1, 20, 17, 0, 0),
        "TEST18": Player("TEST18", "Player 18", "test18@mail.com", "000-000-0018", "test18.jpg", "availability 18", 1, 15, 18, 0, 0),
        "TEST19": Player("TEST19", "Player 19", "test19@mail.com", "000-000-0019", "test19.jpg", "availability 19", 1, 10, 19, 0, 0),
        "TEST20": Player("TEST20", "Player 20", "test20@mail.com", "000-000-0020", "test20.jpg", "availability 20", 1, 5, 20, 0, 0)
    }
    updated_scores = []
    saved_match = None
    created_user = False

    def get_user(self, user_id):
        self.created_user = False
        return self.user_database.get(user_id)

    def in_same_ladder(self, user1_id, user2_id):
        return user2_id != "BAD_USER"

    def create_user(self, user):
        self.user_database[user.user_id] = user
        self.created_user = True
        return user

    def update_user(self, user):
        self.user_database[user.user_id] = user
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
