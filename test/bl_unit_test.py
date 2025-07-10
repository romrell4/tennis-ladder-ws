import unittest
from datetime import datetime, timedelta, date
from unittest.mock import patch

from bl import ManagerImpl
from da import Dao
from domain import ServiceException, Match, User
from firebase_client import FirebaseClient
from pytz import timezone
import fixtures


class Test(unittest.TestCase):
    def setUp(self):
        self.manager = ManagerImpl(FirebaseClient(), Dao())
        self.manager.user = fixtures.user(user_id="USER1", admin=True)

    # region validate_token
    def test_validate_token_with_no_token(self):
        self.manager.user = None
        self.manager.validate_token(None)
        self.assertIsNone(self.manager.user)

    def test_validate_token_throws_error(self):
        def raise_error(_): raise ValueError()

        with patch.object(self.manager.firebase_client, "get_firebase_user", side_effect=raise_error):
            self.manager.user = None
            self.manager.validate_token("bad_token")
            self.assertIsNone(self.manager.user)

    def test_validate_token_when_firebase_user_missing_required_fields(self):
        with patch.object(self.manager.firebase_client, "get_firebase_user", return_value={}) as mock:
            self.manager.user = None
            self.manager.validate_token("token")
            self.assertIsNone(self.manager.user)
        mock.assert_called_once_with("token")

    # noinspection PyUnresolvedReferences
    def test_validate_token_with_new_user(self):
        with patch.object(self.manager.firebase_client, "get_firebase_user", return_value={"user_id": "NEW_FB_ID", "name": "NAME", "email": "EMAIL", "picture": "PICTURE"}):
            with patch.object(self.manager.dao, "get_user", return_value=None):
                with patch.object(self.manager.dao, "create_user") as create_user_mock:
                    self.manager.user = None
                    self.manager.validate_token("")
                    self.assertIsNotNone(self.manager.user)
                    self.assertEqual("NEW_FB_ID", self.manager.user.user_id)
                    self.assertEqual("NAME", self.manager.user.name)
                    self.assertEqual("EMAIL", self.manager.user.email)
                    self.assertIsNone(self.manager.user.phone_number)
                    self.assertEqual("PICTURE", self.manager.user.photo_url)
                    self.assertIsNone(self.manager.user.availability_text)
                    self.assertFalse(self.manager.user.admin)

                create_user_mock.assert_called_once_with(self.manager.user)

    # noinspection PyUnresolvedReferences
    def test_validate_token_with_new_user_without_name(self):
        with patch.object(self.manager.firebase_client, "get_firebase_user", return_value={"user_id": "NEW_FB_ID", "email": "EMAIL", "picture": "PICTURE"}):
            with patch.object(self.manager.dao, "get_user", return_value=None):
                with patch.object(self.manager.dao, "create_user"):
                    self.manager.validate_token("")
        self.assertIsNotNone(self.manager.user)
        self.assertEqual("Unknown", self.manager.user.name)

    def test_validate_token_with_new_user_with_empty_picture(self):
        with patch.object(self.manager.firebase_client, "get_firebase_user", return_value={"user_id": "NEW_FB_ID", "email": "EMAIL", "picture": ""}):
            with patch.object(self.manager.dao, "get_user", return_value=None):
                with patch.object(self.manager.dao, "create_user"):
                    self.manager.validate_token("")
        self.assertIsNotNone(self.manager.user)
        self.assertIsNone(self.manager.user.photo_url)

    def test_validate_token_with_existing_user(self):
        with patch.object(self.manager.firebase_client, "get_firebase_user", return_value={"user_id": "FB_ID"}):
            existing_user = fixtures.user()
            with patch.object(self.manager.dao, "get_user", return_value=existing_user):
                self.manager.validate_token("")
        self.assertEqual(existing_user, self.manager.user)

    # endregion
    # region get_user
    def test_get_user_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.get_user(None), 401, "Unable to authenticate")

    def test_get_user_with_no_user_id_param(self):
        self.assert_error(lambda: self.manager.get_user(None), 400, "No user_id passed in")

    def test_get_user_get_another_player_not_in_your_ladder(self):
        with patch.object(self.manager.dao, "in_same_ladder", return_value=False):
            self.assert_error(lambda: self.manager.get_user("BAD_USER"), 403, "You are only allowed to access profile information for users who are playing in the same ladder as you")

    def test_get_user_get_yourself(self):
        returned_user = fixtures.user()
        with patch.object(self.manager.dao, "get_user", return_value=returned_user):
            user = self.manager.get_user(self.manager.user.user_id)
        self.assertEqual(user, returned_user)

    def test_get_user_get_another_player_in_your_ladder(self):
        returned_user = fixtures.user()
        with patch.object(self.manager.dao, "in_same_ladder", return_value=True):
            with patch.object(self.manager.dao, "get_user", return_value=returned_user):
                user = self.manager.get_user("TEST1")
        self.assertEqual(user, returned_user)

    # endregion
    # region update_user
    def test_update_user_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.update_user(None, None), 401, "Unable to authenticate")

    def test_update_user_with_no_user_id_param(self):
        self.assert_error(lambda: self.manager.update_user(None, None), 400, "No user_id passed in")

    def test_update_user_with_no_user_param(self):
        self.assert_error(lambda: self.manager.update_user("", None), 400, "No user passed in to update")

    def test_update_user_updating_another_user(self):
        self.assert_error(lambda: self.manager.update_user("ANOTHER_USER", {}), 403, "You are only allowed to update your own profile information")

    def test_update_user_specifying_all_info_should_only_update_info_that_can_be_updated(self):
        user = fixtures.user()
        with patch.object(self.manager.dao, "update_user") as update_user_mock:
            with patch.object(self.manager.dao, "get_user", return_value=user):
                returned_user = self.manager.update_user(self.manager.user.user_id, {"user_id": "bad", "name": "new name", "email": "new email", "phone_number": "new phone", "photo_url": "new url", "availability_text": "new availability"})
        self.assertEqual(user, returned_user)

        update_user_mock.assert_called_once()
        saved_user = update_user_mock.call_args.args[0]
        self.assertNotEqual("bad", saved_user.user_id)
        self.assertEqual("new name", saved_user.name)
        self.assertEqual("new email", saved_user.email)
        self.assertEqual("new phone", saved_user.phone_number)
        self.assertEqual("new url", saved_user.photo_url)
        self.assertEqual("new availability", saved_user.availability_text)

    # endregion
    # region get_ladders
    def test_get_ladders_when_not_logged_in_should_return_all_with_all_false_flags(self):
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            fixtures.ladder(1, "Ladder 1", date.today(), date.today(), False),
            fixtures.ladder(2, "Ladder 2", date.today(), date.today(), False),
        ]):
            self.manager.user = None
            ladders = self.manager.get_ladders()
            self.assertEqual(2, len(ladders))
            self.assertEqual(1, ladders[0].ladder_id)
            self.assertFalse(ladders[0].logged_in_user_has_joined)
            self.assertEqual(2, ladders[1].ladder_id)
            self.assertFalse(ladders[1].logged_in_user_has_joined)

    def test_get_ladders_when_not_a_player_in_any_ladder(self):
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            fixtures.ladder(1, "Ladder 1", date.today(), date.today(), False),
            fixtures.ladder(2, "Ladder 2", date.today(), date.today(), False),
        ]):
            with patch.object(self.manager.dao, "get_users_ladder_ids", return_value=[]):
                with patch.object(self.manager.dao, "get_users_admin_ladder_ids", return_value=[]):
                    ladders = self.manager.get_ladders()
                    self.assertEqual(2, len(ladders))
                    self.assertEqual(1, ladders[0].ladder_id)
                    self.assertFalse(ladders[0].logged_in_user_has_joined)
                    self.assertEqual(2, ladders[1].ladder_id)
                    self.assertFalse(ladders[1].logged_in_user_has_joined)

    def test_get_ladders_when_in_a_ladder_should_put_your_ladder_at_the_top_and_have_true_flag(self):
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            fixtures.ladder(1),
            fixtures.ladder(2),
        ]):
            with patch.object(self.manager.dao, "get_users_ladder_ids", return_value=[2]):
                with patch.object(self.manager.dao, "get_users_admin_ladder_ids", return_value=[]):
                    self.manager.user = User("TEST1", "User", "user@test.com", "555-555-5555", "user.jpg", "availability", False)
                    ladders = self.manager.get_ladders()
                    self.assertEqual(2, len(ladders))
                    self.assertEqual(2, ladders[0].ladder_id)
                    self.assertTrue(ladders[0].logged_in_user_has_joined)
                    self.assertEqual(1, ladders[1].ladder_id)
                    self.assertFalse(ladders[1].logged_in_user_has_joined)

    def test_get_ladders_as_uber_admin_should_return_admin_for_all_ladders(self):
        self.manager.user = fixtures.user(admin=True)
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            fixtures.ladder(ladder_id=1),
            fixtures.ladder(ladder_id=2),
            fixtures.ladder(ladder_id=3),
        ]):
            with patch.object(self.manager.dao, "get_users_ladder_ids", return_value=[]):
                ladders = self.manager.get_ladders()
                self.assertEqual(3, len(ladders))
                self.assertTrue(ladders[0].logged_in_user_is_admin)
                self.assertTrue(ladders[1].logged_in_user_is_admin)
                self.assertTrue(ladders[2].logged_in_user_is_admin)

    def test_get_ladders_should_return_ladder_admins(self):
        self.manager.user = fixtures.user(admin=False)
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            fixtures.ladder(ladder_id=1),
            fixtures.ladder(ladder_id=2),
            fixtures.ladder(ladder_id=3),
        ]):
            with patch.object(self.manager.dao, "get_users_ladder_ids", return_value=[]):
                with patch.object(self.manager.dao, "get_users_admin_ladder_ids", return_value=[1, 2]):
                    ladders = self.manager.get_ladders()
                    self.assertEqual(3, len(ladders))
                    self.assertTrue(ladders[0].logged_in_user_is_admin)
                    self.assertTrue(ladders[1].logged_in_user_is_admin)
                    self.assertFalse(ladders[2].logged_in_user_is_admin)

    # endregion
    # region add_player_to_ladder
    def test_add_player_to_ladder_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.add_player_to_ladder(None, None), 401, "Unable to authenticate")

    def test_add_player_to_ladder_with_null_ladder_id(self):
        self.assert_error(lambda: self.manager.add_player_to_ladder(None, None), 400, "Null ladder_id param")

    def test_add_player_to_ladder_with_non_existent_ladder_id(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=None):
            self.assert_error(lambda: self.manager.add_player_to_ladder(0, None), 404, "No ladder with id: '0'")

    def test_add_player_to_ladder_with_no_code_when_a_code_is_required(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=fixtures.ladder()):
            with patch.object(self.manager.dao, "get_ladder_code", return_value="good"):
                self.assert_error(lambda: self.manager.add_player_to_ladder(1, None), 400, "The code provided does not match the code of the ladder. If you believe this in error, please contact the ladder's sponsor.")

    def test_add_player_to_ladder_with_a_bad_code(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=fixtures.ladder()):
            with patch.object(self.manager.dao, "get_ladder_code", return_value="good"):
                self.assert_error(lambda: self.manager.add_player_to_ladder(1, "bad"), 400, "The code provided does not match the code of the ladder. If you believe this in error, please contact the ladder's sponsor.")

    def test_add_player_to_ladder_with_a_valid_code_should_create_player_and_return_all_ladder_players(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=fixtures.ladder()):
            with patch.object(self.manager.dao, "get_ladder_code", return_value="good"):
                with patch.object(self.manager.dao, "create_player") as create_player_mock:
                    with patch.object(self.manager.dao, "get_players", return_value=[fixtures.player()]) as get_players_mock:
                        players = self.manager.add_player_to_ladder(1, "good")
        create_player_mock.assert_called_once_with(1, self.manager.user.user_id)
        get_players_mock.assert_called_once_with(1)
        self.assertEqual(1, len(players))

    def test_add_player_to_ladder_without_a_code_when_no_code_is_required_should_create_player(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=fixtures.ladder()):
            with patch.object(self.manager.dao, "get_ladder_code", return_value=None):
                with patch.object(self.manager.dao, "create_player") as create_player_mock:
                    with patch.object(self.manager.dao, "get_players", return_value=[]):
                        self.manager.add_player_to_ladder(2, None)
        create_player_mock.assert_called_once()

    def test_add_player_to_ladder_with_a_code_when_no_code_is_required_should_create_player(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=fixtures.ladder()):
            with patch.object(self.manager.dao, "get_ladder_code", return_value=None):
                with patch.object(self.manager.dao, "create_player") as create_player_mock:
                    with patch.object(self.manager.dao, "get_players", return_value=[]):
                        self.manager.add_player_to_ladder(2, "bad")
        create_player_mock.assert_called_once()

    # endregion
    # region update_player_order
    def test_update_player_order_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.update_player_order(None, False, None), 401, "Unable to authenticate")

    def test_update_player_order_with_no_ladder_id_param(self):
        self.assert_error(lambda: self.manager.update_player_order(None, False, None), 400, "No ladder_id passed in")

    def test_update_player_order_when_not_an_admin(self):
        self.manager.user = fixtures.user(user_id="me", admin=False)
        with patch.object(self.manager.dao, "get_ladder_admins", return_value=["not me"]):
            self.assert_error(lambda: self.manager.update_player_order(1, False, None), 403, "Only admins can update player orders")

    def test_update_player_order_with_no_players_param(self):
        self.assert_error(lambda: self.manager.update_player_order(1, False, None), 400, "No players passed in")

    def test_update_player_order_when_ladder_doesnt_exist(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=None):
            self.assert_error(lambda: self.manager.update_player_order(1, False, []), 404, "No ladder with ID: 1")

    def test_update_player_order_when_ladder_already_started(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            self.assert_error(lambda: self.manager.update_player_order(1, False, []), 403, "You can only update player order before the ladder has started")

    def test_update_player_order_without_generating_borrowed_points_should_update_order_and_return_players(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=pre_open_ladder()):
            with patch.object(self.manager.dao, "update_player_order") as update_player_order_mock:
                with patch.object(self.manager.dao, "get_players", return_value=[]):
                    response = self.manager.update_player_order(1, False, [{"user": {"user_id": "1"}}, {"user": {"user_id": "2"}}])
        update_player_order_mock.assert_called_once_with(1, [["2", 1], ["1", 2]])
        self.assertEqual([], response)

    def test_update_player_order_with_generating_borrowed_points_should_update_order_and_borrowed_points_and_return_players(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=pre_open_ladder(weeks_for_borrowed_points=5)):
            with patch.object(self.manager.dao, "update_player_order") as update_player_order_mock:
                with patch.object(self.manager.dao, "update_all_borrowed_points") as update_all_borrowed_points_mock:
                    with patch.object(self.manager.dao, "get_players", return_value=[]):
                        response = self.manager.update_player_order(1, True, [{"user": {"user_id": "1"}}, {"user": {"user_id": "2"}}])
        update_player_order_mock.assert_called_once_with(1, [["2", 1], ["1", 2]])
        update_all_borrowed_points_mock.assert_called_once_with(1, [["2", 5], ["1", 10]])
        self.assertEqual([], response)

    # endregion
    # region update_player
    def test_update_player_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.update_player(None, None, None), 401, "Unable to authenticate")

    def test_update_player_with_no_ladder_id_param(self):
        self.assert_error(lambda: self.manager.update_player(None, None, None), 400, "No ladder_id passed in")

    def test_update_player_when_not_an_admin(self):
        self.manager.user = fixtures.user(user_id="me", admin=False)
        with patch.object(self.manager.dao, "get_ladder_admins", return_value=["not me"]):
            self.assert_error(lambda: self.manager.update_player(0, None, None), 403, "Only admins can update players")

    def test_update_player_with_no_user_id_param(self):
        self.assert_error(lambda: self.manager.update_player(-1, None, None), 400, "No user_id passed in")

    def test_update_player_with_no_player_param(self):
        self.assert_error(lambda: self.manager.update_player(-1, "-1", None), 400, "No player passed in")

    def test_update_player_when_ladder_doesnt_exist(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=None):
            self.assert_error(lambda: self.manager.update_player(-1, "-1", {}), 404, "No ladder with ID: -1")

    def test_update_player_before_ladder_starts(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=pre_open_ladder()):
            self.assert_error(lambda: self.manager.update_player(-1, "-1", {}), 403, "You can only update borrowed points after the ladder has started")

    def test_update_player_with_a_player_param_without_borrowed_points(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            self.assert_error(lambda: self.manager.update_player(-1, "-1", {}), 400, "New player has no borrowed points")
            self.assert_error(lambda: self.manager.update_player(-1, "-1", {"borrowed_points": None}), 400, "New player has no borrowed points")

    def test_update_player_with_a_borrowed_points_value_that_doesnt_exist_on_another_player(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_players", return_value=[fixtures.player(borrowed_points=4), fixtures.player(borrowed_points=8)]):
                self.assert_error(lambda: self.manager.update_player(1, "2", {"borrowed_points": 5}), 400, "You must assign a value that is already assigned to another player in the ladder")

    def test_update_player_with_new_borrowed_points_should_update_and_return_players(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_players", return_value=[fixtures.player(borrowed_points=4), fixtures.player(borrowed_points=8)]):
                with patch.object(self.manager.dao, "update_borrowed_points") as update_borrowed_points_mock:
                    self.manager.update_player(1, "2", {"borrowed_points": 8})
        update_borrowed_points_mock.assert_called_once_with(1, "2", 8)

    # endregion
    # region get_matches
    def test_get_matches_adds_players_to_all_matches(self):
        with patch.object(self.manager.dao, "get_matches", return_value=[fixtures.match(match_id=1, winner_id="TEST1", loser_id="TEST2")]):
            with patch.object(self.manager.dao, "get_players", return_value=[
                fixtures.player(user_=fixtures.user(user_id="TEST1", name="Player 1")),
                fixtures.player(user_=fixtures.user(user_id="TEST2", name="Player 2")),
            ]):
                matches = self.manager.get_matches(1, "TEST1")
        self.assertIsNotNone(matches)
        self.assertEqual(1, len(matches))
        self.assertEqual(1, matches[0].match_id)
        self.assertEqual("TEST1", matches[0].winner.user.user_id)
        self.assertEqual("Player 1", matches[0].winner.user.name)
        self.assertEqual("TEST2", matches[0].loser.user.user_id)
        self.assertEqual("Player 2", matches[0].loser.user.name)

    # endregion
    # region report_match
    def test_report_match_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.report_match(0, {}), 401, "Unable to authenticate")

    def test_report_match_with_a_null_ladder_id_param(self):
        self.assert_error(lambda: self.manager.report_match(None, None), 400, "Null ladder_id param")

    def test_report_match_with_a_null_match_param(self):
        self.assert_error(lambda: self.manager.report_match(0, None), 400, "Null match param")

    def test_report_match_with_a_non_existent_ladder_id(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=None):
            self.assert_error(lambda: self.manager.report_match(0, {}), 404, "No ladder with id: '0'")

    def test_report_match_before_the_ladder_is_open(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=pre_open_ladder()):
            self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST0", "TEST0", 0, 0, 0, 0)), 400, "This ladder is not currently open. You can only report matches between the ladder's start and end dates")

    def test_report_match_after_the_ladder_is_closed(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=fixtures.ladder(start_date=date.today() - timedelta(days=2), end_date=date.today() - timedelta(days=1))):
            self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST0", "TEST0", 0, 0, 0, 0)), 400, "This ladder is not currently open. You can only report matches between the ladder's start and end dates")

    def test_report_match_with_a_winner_and_loser_not_in_the_specified_ladder(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_player", return_value=None):
                self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST0", "TEST1", 6, 0, 6, 0)), 400, "No user with id: 'TEST0'")
            with patch.object(self.manager.dao, "get_player", side_effect=[fixtures.player(), None]):
                self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST1", "TEST0", 6, 0, 6, 0)), 400, "No user with id: 'TEST0'")

    def test_report_match_when_each_player_has_already_played_a_match_that_day(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_player", return_value=fixtures.player()):
                with patch.object(self.manager.dao, "get_matches", return_value=[fixtures.match(match_date=datetime.now(tz=timezone("US/Mountain")), winner_id="TEST1", loser_id="TEST2")]):
                    self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST1", "TEST3", 6, 0, 6, 0)), 400, "Reported winner has already played a match today. Only one match can be played each day.")
                    self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST2", "TEST3", 6, 0, 6, 0)), 400, "Reported winner has already played a match today. Only one match can be played each day.")
                    self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST3", "TEST1", 6, 0, 6, 0)), 400, "Reported loser has already played a match today. Only one match can be played each day.")
                    self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST3", "TEST2", 6, 0, 6, 0)), 400, "Reported loser has already played a match today. Only one match can be played each day.")

    def test_report_match_when_the_two_have_already_played_the_max_number_of_times(self):
        test_match = fixtures.match(match_date=datetime.today() - timedelta(days=1), winner_id="TEST1", loser_id="TEST2")
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_player", return_value=fixtures.player()):
                with patch.object(self.manager.dao, "get_matches", return_value=[test_match] * 5):
                    self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST1", "TEST2", 6, 0, 6, 0)), 400, "Players have already played 5 times.")
                    self.assert_error(lambda: self.manager.report_match(1, create_match_dict("TEST2", "TEST1", 6, 0, 6, 0)), 400, "Players have already played 5 times.")

    @patch.object(Match, "calculate_scores", return_value=(10, 5))
    def test_report_match_valid_match_should_update_player_scores_and_create_match_with_new_date(self, _):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_match", return_value=fixtures.match()):
                with patch.object(self.manager.dao, "get_player", return_value=fixtures.player()):
                    with patch.object(self.manager.dao, "get_matches", return_value=[]):
                        with patch.object(self.manager.dao, "update_earned_points") as update_earned_points_mock:
                            with patch.object(self.manager.dao, "create_match", return_value=fixtures.match(winner_id="TEST1", loser_id="TEST2")) as create_match_mock:
                                with patch.object(self.manager.dao, "get_players", return_value=[
                                    fixtures.player(user_=fixtures.user(user_id="TEST1")),
                                    fixtures.player(user_=fixtures.user(user_id="TEST2"))
                                ]):
                                    match = self.manager.report_match(1, create_match_dict("TEST1", "TEST2", 6, 0, 6, 0))
        self.assertIsNotNone(match)
        self.assertEqual(2, update_earned_points_mock.call_count)
        update_earned_points_mock.assert_any_call(1, "TEST1", 10)
        update_earned_points_mock.assert_any_call(1, "TEST2", 5)
        create_match_mock.assert_called_once()
        saved_match = create_match_mock.call_args.args[0]
        self.assertIsNotNone(saved_match)
        self.assertIsNotNone(saved_match.match_date)

    def test_report_match_where_players_are_too_far_apart_when_distance_penalty_off_should_create_match(self):
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder(distance_penalty_on=False)):
            with patch.object(self.manager.dao, "get_player", side_effect=[
                fixtures.player(ranking=1),
                fixtures.player(ranking=17),
            ]):
                with patch.object(self.manager.dao, "get_matches", return_value=[]):
                    with patch.object(self.manager.dao, "update_earned_points"):
                        with patch.object(self.manager.dao, "create_match", return_value=fixtures.match(winner_id="TEST1", loser_id="TEST2")) as create_match_mock:
                            with patch.object(self.manager.dao, "get_players", return_value=[
                                fixtures.player(user_=fixtures.user(user_id="TEST1", name="Player 1")),
                                fixtures.player(user_=fixtures.user(user_id="TEST2", name="Player 2")),
                            ]):
                                self.manager.report_match(1, create_match_dict("TEST1", "TEST17", 6, 0, 6, 0))
        create_match_mock.assert_called_once()

    def test_report_match_when_you_have_played_the_max_but_not_with_this_opponent_should_create_match(self):
        test_match = fixtures.match(match_date=datetime.now() - timedelta(days=1), winner_id="TEST1", loser_id="TEST2")
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_player", return_value=fixtures.player()):
                with patch.object(self.manager.dao, "get_matches", return_value=[test_match] * 5):
                    with patch.object(self.manager.dao, "update_earned_points"):
                        with patch.object(self.manager.dao, "create_match", return_value=fixtures.match(winner_id="TEST1", loser_id="TEST2")) as create_match_mock:
                            with patch.object(self.manager.dao, "get_players", return_value=[
                                fixtures.player(user_=fixtures.user(user_id="TEST1", name="Player 1")),
                                fixtures.player(user_=fixtures.user(user_id="TEST2", name="Player 2")),
                            ]):
                                self.manager.report_match(1, create_match_dict("TEST1", "TEST3", 6, 0, 6, 0))
        create_match_mock.assert_called_once()

    def test_report_match_when_you_have_played_your_opponent_one_less_than_the_max_number_of_times_should_create_match(self):
        test_match = fixtures.match(match_date=datetime.now() - timedelta(days=1), winner_id="TEST1", loser_id="TEST2")
        with patch.object(self.manager.dao, "get_ladder", return_value=open_ladder()):
            with patch.object(self.manager.dao, "get_player", return_value=fixtures.player()):
                with patch.object(self.manager.dao, "get_matches", return_value=[test_match] * 4):
                    with patch.object(self.manager.dao, "update_earned_points"):
                        with patch.object(self.manager.dao, "create_match", return_value=fixtures.match(winner_id="TEST1", loser_id="TEST2")) as create_match_mock:
                            with patch.object(self.manager.dao, "get_players", return_value=[
                                fixtures.player(user_=fixtures.user(user_id="TEST1", name="Player 1")),
                                fixtures.player(user_=fixtures.user(user_id="TEST2", name="Player 2")),
                            ]):
                                self.manager.report_match(1, create_match_dict("TEST1", "TEST2", 6, 0, 6, 0))
        create_match_mock.assert_called_once()

    # endregion
    # region update_match
    def test_update_match_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.update_match_scores(0, 0, {}), 401, "Unable to authenticate")

    def test_update_match_with_a_null_ladder_id(self):
        self.assert_error(lambda: self.manager.update_match_scores(None, 0, {}), 400, "No ladder_id passed in")

    def test_update_match_when_the_user_isnt_an_admin(self):
        self.manager.user = fixtures.user(user_id="me", admin=False)
        with patch.object(self.manager.dao, "get_ladder_admins", return_value=["not me"]):
            self.assert_error(lambda: self.manager.update_match_scores(0, 0, {}), 403, "Only admins can update matches")

    def test_update_match_with_a_null_match_id(self):
        self.assert_error(lambda: self.manager.update_match_scores(0, None, None), 400, "Null match_id param")

    def test_update_match_with_a_null_match(self):
        self.assert_error(lambda: self.manager.update_match_scores(0, 0, None), 400, "Null match param")

    def test_update_match_with_a_match_id_that_doesnt_exist(self):
        with patch.object(self.manager.dao, "get_match", return_value=None):
            self.assert_error(lambda: self.manager.update_match_scores(0, 0, {}), 404, "No match with ID: 0")

    def test_update_match_with_valid_match_should_update_match_with_new_points_as_well_as_players_points_and_return_updated_match(self):
        existing_match = fixtures.match(
            ladder_id=1,
            match_date=datetime(2020, 1, 2, 3, 4, 5),
            winner_id='TEST1',
            loser_id='TEST2',
            winner_set1_score=6,
            loser_set1_score=0,
            winner_set2_score=0,
            loser_set2_score=6,
            winner_set3_score=6,
            loser_set3_score=0,
            winner_points=33,
            loser_points=6
        )
        with patch.object(self.manager.dao, "get_match", return_value=existing_match):
            with patch.object(self.manager.dao, "update_match") as update_match_mock:
                with patch.object(self.manager.dao, "update_earned_points") as update_earned_points_mock:
                    with patch.object(self.manager.dao, "get_players", return_value=[
                        fixtures.player(user_=fixtures.user(user_id="TEST1", name="Player 1")),
                        fixtures.player(user_=fixtures.user(user_id="TEST2", name="Player 2")),
                    ]):
                        returned_match = self.manager.update_match_scores(0, 1, create_match_dict('BAD1', 'BAD2', 6, 0, 0, 6, 6, 1, ladder_id=2))
        # Test that returned value has winner/loser info
        self.assertEqual("Player 1", returned_match.winner.user.name)
        self.assertEqual("Player 2", returned_match.loser.user.name)

        # Test that the update was made
        update_match_mock.assert_called_once()
        updated_match = update_match_mock.call_args.args[0]
        # Test values that should have updated
        self.assertEqual(6, updated_match.winner_set1_score)
        self.assertEqual(0, updated_match.loser_set1_score)
        self.assertEqual(0, updated_match.winner_set2_score)
        self.assertEqual(6, updated_match.loser_set2_score)
        self.assertEqual(6, updated_match.winner_set3_score)
        self.assertEqual(1, updated_match.loser_set3_score)
        self.assertEqual(32, updated_match.winner_points)
        self.assertEqual(7, updated_match.loser_points)
        # Test values that shouldn't update
        self.assertEqual(1, updated_match.ladder_id)
        self.assertEqual(datetime(2020, 1, 2, 3, 4, 5, tzinfo=timezone("US/Mountain")), updated_match.match_date)
        self.assertEqual("TEST1", updated_match.winner_id)
        self.assertEqual("TEST2", updated_match.loser_id)

        # Test earned points updated
        self.assertEqual(2, update_earned_points_mock.call_count)
        update_earned_points_mock.assert_any_call(1, "TEST1", -1)
        update_earned_points_mock.assert_any_call(1, "TEST2", 1)

    def test_update_match_when_the_winner_would_go_below_the_min_amount_should_stay_at_min_amount(self):
        existing_match = fixtures.match(ladder_id=1, winner_id='TEST1', loser_id='TEST2', winner_set1_score=6, loser_set1_score=0, winner_set2_score=6, loser_set2_score=0, winner_points=Match.MIN_WINNER_POINTS, loser_points=0)
        with patch.object(self.manager.dao, "get_match", return_value=existing_match):
            with patch.object(self.manager.dao, "update_match") as update_match_mock:
                with patch.object(self.manager.dao, "update_earned_points") as update_earned_points_mock:
                    with patch.object(self.manager.dao, "get_players", return_value=[
                        fixtures.player(user_=fixtures.user(user_id="TEST1", name="Player 1")),
                        fixtures.player(user_=fixtures.user(user_id="TEST2", name="Player 2")),
                    ]):
                        self.manager.update_match_scores(0, 1, create_match_dict('BAD1', 'BAD2', 6, 0, 6, 1))
        update_match_mock.assert_called_once()
        updated_match = update_match_mock.call_args.args[0]
        self.assertIsNotNone(updated_match)
        self.assertEqual(Match.MIN_WINNER_POINTS, updated_match.winner_points)  # Can't go below the min amount, even though you're losing points
        self.assertEqual(1, updated_match.loser_points)
        self.assertEqual(2, update_earned_points_mock.call_count)
        update_earned_points_mock.assert_any_call(1, "TEST1", 0)
        update_earned_points_mock.assert_any_call(1, "TEST2", 1)

    # endregion
    # region get_score_diff
    def test_score_diff(self):
        def create_match(winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score=None, loser_set3_score=None):
            return fixtures.match(
                winner_set1_score=winner_set1_score,
                loser_set1_score=loser_set1_score,
                winner_set2_score=winner_set2_score,
                loser_set2_score=loser_set2_score,
                winner_set3_score=winner_set3_score,
                loser_set3_score=loser_set3_score
            )

        self.assertEqual((-1, 1), self.manager.get_score_diff(create_match(6, 0, 6, 0), create_match(6, 0, 6, 1)))
        self.assertEqual((-5, 5), self.manager.get_score_diff(create_match(6, 0, 6, 0), create_match(6, 0, 7, 5)))
        self.assertEqual((6, -6), self.manager.get_score_diff(create_match(7, 6, 6, 0), create_match(6, 0, 6, 0)))
        self.assertEqual((-6, 6), self.manager.get_score_diff(create_match(6, 0, 6, 0), create_match(6, 0, 0, 6, 10, 0)))
        self.assertEqual((-5, 5), self.manager.get_score_diff(create_match(6, 2, 6, 2), create_match(6, 0, 6, 7, 10, 4)))
        self.assertEqual((-6, 6), self.manager.get_score_diff(create_match(6, 2, 6, 2), create_match(6, 0, 6, 7, 10, 5)))
        self.assertEqual((9, -9), self.manager.get_score_diff(create_match(6, 0, 0, 6, 6, 3), create_match(6, 0, 6, 0)))

    # endregion
    # region delete_match
    def test_delete_match_when_not_logged_in(self):
        self.manager.user = None
        self.assert_error(lambda: self.manager.delete_match(0, 0), 401, "Unable to authenticate")

    def test_delete_match_with_a_null_ladder_id(self):
        self.assert_error(lambda: self.manager.delete_match(None, 0), 400, "No ladder_id passed in")

    def test_delete_match_when_not_an_admin(self):
        self.manager.user = fixtures.user(user_id="me", admin=False)
        with patch.object(self.manager.dao, "get_ladder_admins", return_value=["not me"]):
            self.assert_error(lambda: self.manager.delete_match(0, 0), 403, "Only admins can delete matches")

    def test_delete_match_with_a_null_match_id(self):
        self.assert_error(lambda: self.manager.delete_match(0, None), 400, "Null match_id param")

    def test_delete_match_that_doesnt_exist_should_do_nothing_but_succeed(self):
        with patch.object(self.manager.dao, "get_match", return_value=None):
            with patch.object(self.manager.dao, "update_earned_points") as update_earned_points_mock:
                with patch.object(self.manager.dao, "delete_match") as delete_match_mock:
                    self.manager.delete_match(0, -1)
        update_earned_points_mock.assert_not_called()
        delete_match_mock.assert_not_called()

    def test_delete_match_valid_should_delete_match_and_reverse_players_earned_points(self):
        with patch.object(self.manager.dao, "get_match", return_value=fixtures.match(match_id=123, ladder_id=1, winner_id="TEST1", loser_id="TEST2", winner_points=33, loser_points=6)):
            with patch.object(self.manager.dao, "update_earned_points") as update_earned_points_mock:
                with patch.object(self.manager.dao, "delete_match") as delete_match_mock:
                    self.manager.delete_match(0, 1)
        # Test that match was deleted
        delete_match_mock.assert_called_once_with(1)
        # Test earned points updated
        self.assertEqual(2, update_earned_points_mock.call_count)
        update_earned_points_mock.assert_any_call(1, "TEST1", -33)
        update_earned_points_mock.assert_any_call(1, "TEST2", -6)

    def test_delete_match_valid_as_a_ladder_admin_should_delete_match(self):
        self.manager.user = fixtures.user(user_id="me", admin=False)
        with patch.object(self.manager.dao, "get_ladder_admins", return_value=["not me", "me"]):
            with patch.object(self.manager.dao, "get_match", return_value=fixtures.match(match_id=123, ladder_id=1, winner_id="TEST1", loser_id="TEST2", winner_points=33, loser_points=6)):
                with patch.object(self.manager.dao, "update_earned_points"):
                    with patch.object(self.manager.dao, "delete_match") as delete_match_mock:
                        self.manager.delete_match(0, 1)
        # Test that match was deleted
        delete_match_mock.assert_called_once_with(1)

    def test_decrement_borrowed_points_with_all_invalid_ladders_should_make_no_updates(self):
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            # Hasn't started yet
            fixtures.ladder(start_date=date.today() + timedelta(days=1), end_date=date.today() + timedelta(days=2)),
            # Already ended
            fixtures.ladder(start_date=date.today() - timedelta(days=1), end_date=date.today() - timedelta(minutes=1)),
            # Open, but doesn't use borrowed points
            fixtures.ladder(weeks_for_borrowed_points=0),
            # Open, uses borrowed points, but has already been updated this week
            fixtures.ladder(
                # Ladder started a week ago
                start_date=date.today() - timedelta(weeks=1),
                end_date=date.today() + timedelta(weeks=12),
                weeks_for_borrowed_points=5,
                # We've already decremented for week 4
                weeks_for_borrowed_points_left=4
            )
        ]):
            with patch.object(self.manager.dao, "decrement_borrowed_points") as decrement_borrowed_points_mock:
                with patch.object(self.manager.dao, "update_ladder") as update_ladder_mock:
                    self.manager.decrement_borrowed_points()
        decrement_borrowed_points_mock.assert_not_called()
        update_ladder_mock.assert_not_called()

    def test_decrement_borrowed_points_with_multiple_eligible_ladders_should_update_points_and_ladder_correctly(self):
        with patch.object(self.manager.dao, "get_ladders", return_value=[
            # Normal case (hasn't been updated for this week yet)
            fixtures.ladder(
                ladder_id=1,
                # Ladder started a week ago
                start_date=date.today() - timedelta(weeks=1),
                end_date=date.today() + timedelta(weeks=12),
                weeks_for_borrowed_points=5,
                # Haven't updated for week 4 yet
                weeks_for_borrowed_points_left=5
            ),
            # Case where we missed a week due to error or something
            fixtures.ladder(
                ladder_id=2,
                # Ladder started a week ago
                start_date=date.today() - timedelta(weeks=2),
                end_date=date.today() + timedelta(weeks=12),
                weeks_for_borrowed_points=5,
                # Haven't updated for week 4 yet
                weeks_for_borrowed_points_left=5
            ),
        ]):
            with patch.object(self.manager.dao, "decrement_borrowed_points") as decrement_borrowed_points_mock:
                with patch.object(self.manager.dao, "update_ladder") as update_ladder_mock:
                    self.manager.decrement_borrowed_points()
        self.assertEqual(2, decrement_borrowed_points_mock.call_count)
        self.assertEqual((1, 5, 4), decrement_borrowed_points_mock.mock_calls[0].args)
        self.assertEqual((2, 5, 3), decrement_borrowed_points_mock.mock_calls[1].args)
        self.assertEqual(2, update_ladder_mock.call_count)
        self.assertEqual(4, update_ladder_mock.mock_calls[0].args[0].weeks_for_borrowed_points_left)
        self.assertEqual(3, update_ladder_mock.mock_calls[1].args[0].weeks_for_borrowed_points_left)

    # endregion
    # region utils
    def assert_error(self, block, status_code, error_message):
        with self.assertRaises(ServiceException) as e:
            block()
        self.assertEqual(error_message, e.exception.error_message)
        self.assertEqual(status_code, e.exception.status_code)
    # endregion


def create_match_dict(winner_id, loser_id, winner_set1_score, loser_set1_score, winner_set2_score, loser_set2_score, winner_set3_score=None, loser_set3_score=None, ladder_id=1, match_date=None):
    return {
        "ladder_id": ladder_id,
        "match_date": match_date,
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


def open_ladder(distance_penalty_on=False):
    return fixtures.ladder(start_date=date.today() - timedelta(days=1), end_date=date.today() + timedelta(days=1), distance_penalty_on=distance_penalty_on)


def pre_open_ladder(weeks_for_borrowed_points=0):
    return fixtures.ladder(start_date=date.today() + timedelta(days=1), end_date=date.today() + timedelta(days=2), weeks_for_borrowed_points=weeks_for_borrowed_points)
