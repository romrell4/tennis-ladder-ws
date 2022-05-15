import unittest
from typing import Dict
from unittest.mock import patch

import fixtures
from bl import Manager
from src import handler
from src.domain import *
from datetime import datetime, date


class Test(unittest.TestCase):
    def setUp(self):
        self.handler = handler.Handler(Manager())

    def test_decrement_borrowed_points(self):
        with patch.object(self.handler.manager, "decrement_borrowed_points") as decrement_borrowed_points_mock:
            self.handler.handle({"decrement-borrowed-points": True})
        decrement_borrowed_points_mock.assert_called_once()

    def test_token_can_handle_any_casing(self):
        with patch.object(self.handler.manager, "validate_token") as validate_token_mock:
            self.handler.handle(create_event("/bad", headers={"x-firebase-token": "token"}))
        validate_token_mock.assert_called_once_with("token")

        with patch.object(self.handler.manager, "validate_token") as validate_token_mock:
            self.handler.handle(create_event("/bad", headers={"X-Firebase-Token": "token"}))
        validate_token_mock.assert_called_once_with("token")

    def test_success_response_with_complex_body_is_serialized_correctly(self):
        class NestedObject:
            def __init__(self):
                self.key = "value"

        class TestObject:
            def __init__(self):
                self.datetime = datetime(2020, 1, 1, 1, 0, 0)
                self.date = date(2021, 12, 25)
                self.nested_object = NestedObject()

        with patch.object(self.handler.manager, "get_ladders", return_value=[TestObject()]):
            response = self.handler.handle(create_event("/ladders"))
        self.assertEqual(200, response["statusCode"])
        self.assertEqual("""[{"datetime": "2020-01-01T01:00:00Z", "date": "2021-12-25", "nested_object": {"key": "value"}}]""", response["body"])

    def test_user_serialization_contract(self):
        with patch.object(self.handler.manager, "get_ladders", return_value=[User("user_id", "name", "email", "phone_number", "photo_url", "availability_text", True)]):
            response = self.handler.handle(create_event("/ladders"))
        self.assertEqual("""[{"user_id": "user_id", "name": "name", "email": "email", "phone_number": "phone_number", "photo_url": "photo_url", "availability_text": "availability_text", "admin": true}]""", response["body"])

    def test_ladder_serialization_contract(self):
        with patch.object(self.handler.manager, "get_ladders", return_value=[Ladder(1, "name", date(2020, 1, 1), date(2021, 2, 3), False, 5, True)]):
            response = self.handler.handle(create_event("/ladders"))
        self.assertEqual("""[{"ladder_id": 1, "name": "name", "start_date": "2020-01-01", "end_date": "2021-02-03", "distance_penalty_on": false, "weeks_for_borrowed_points": 5, "logged_in_user_has_joined": true}]""", response["body"])

    def test_player_serialization_contract(self):
        with patch.object(self.handler.manager, "get_ladders", return_value=[Player("user_id", "name", "email", "phone_number", "photo_url", "availability_text", True, 1, 23, 12, 11, 3, 6, 2)]):
            response = self.handler.handle(create_event("/ladders"))
        self.assertEqual(
            """[{"user": {"user_id": "user_id", "name": "name", "email": "email", "phone_number": "phone_number", "photo_url": "photo_url", "availability_text": "availability_text", "admin": true}, "ladder_id": 1, "score": 23, "earned_points": 12, "borrowed_points": 11, "ranking": 3, "wins": 6, "losses": 2}]""",
            response["body"]
        )

    def test_match_serialization_contract(self):
        with patch.object(self.handler.manager, "get_ladders", return_value=[
            Match(1, 2, datetime(2020, 1, 2, 3, 4, 5), "winner_id", "loser_id", 6, 0, 5, 7, 10, 8, 24, 12, fixtures.player(user_=fixtures.user(user_id="winner_id"), ladder_id=2),
                  fixtures.player(user_=fixtures.user(user_id="loser_id"), ladder_id=2))]):
            response = self.handler.handle(create_event("/ladders"))
        self.assertEqual(
            """[{"match_id": 1, "ladder_id": 2, "match_date": "2020-01-02T03:04:05Z", "winner_id": "winner_id", "loser_id": "loser_id", "winner_set1_score": 6, "loser_set1_score": 0, "winner_set2_score": 5, "loser_set2_score": 7, "winner_set3_score": 10, "loser_set3_score": 8, "winner_points": 24, "loser_points": 12, "winner": {"user": {"user_id": "winner_id", "name": "", "email": "", "phone_number": null, "photo_url": null, "availability_text": null, "admin": false}, "ladder_id": 2, "score": 0, "earned_points": 0, "borrowed_points": 0, "ranking": 0, "wins": 0, "losses": 0}, "loser": {"user": {"user_id": "loser_id", "name": "", "email": "", "phone_number": null, "photo_url": null, "availability_text": null, "admin": false}, "ladder_id": 2, "score": 0, "earned_points": 0, "borrowed_points": 0, "ranking": 0, "wins": 0, "losses": 0}}]""",
            response["body"]
        )

    def test_success_response_with_no_body_has_no_body(self):
        with patch.object(self.handler.manager, "get_ladders", return_value=None):
            response = self.handler.handle(create_event("/ladders"))
        self.assertEqual(200, response["statusCode"])
        self.assertIsNone(response["body"])

    def test_error_response_serialized_correctly(self):
        response = self.handler.handle(create_event("/bad"))
        self.assertEqual(500, response["statusCode"])
        self.assertEqual("""{"error": "Invalid path: '/bad GET'"}""", response["body"])

    def test_get_user(self):
        with patch.object(self.handler.manager, "get_user", return_value={}) as get_user_mock:
            self.handler.handle(create_event("/users/{user_id}", {"user_id": "abc"}))
        get_user_mock.assert_called_once_with("abc")

    def test_update_user(self):
        with patch.object(self.handler.manager, "update_user", return_value={}) as update_user_mock:
            self.handler.handle(create_event("/users/{user_id}", {"user_id": "abc"}, "PUT", "{}"))
        update_user_mock.assert_called_once_with("abc", {})

    def test_get_ladders(self):
        with patch.object(self.handler.manager, "get_ladders", return_value={}) as get_ladders_mock:
            self.handler.handle(create_event("/ladders"))
        get_ladders_mock.assert_called_once_with()

    def test_get_players(self):
        with patch.object(self.handler.manager, "get_players", return_value={}) as get_players_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}))
        get_players_mock.assert_called_once_with(1)

    def test_create_player_without_code_should_default_to_none(self):
        with patch.object(self.handler.manager, "add_player_to_ladder", return_value={}) as add_player_to_ladder_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}, "POST"))
        add_player_to_ladder_mock.assert_called_once_with(1, None)

    def test_create_player_with_code_should_pass_it_through(self):
        with patch.object(self.handler.manager, "add_player_to_ladder", return_value={}) as add_player_to_ladder_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/players", {"ladder_id": "1"}, "POST", query_params={"code": "good"}))
        add_player_to_ladder_mock.assert_called_once_with(1, "good")

    def test_update_player_order_without_generate_borrowed_points_query_param_should_default_to_false(self):
        with patch.object(self.handler.manager, "update_player_order", return_value=[]) as update_player_order_mock:
            self.handler.handle(create_event(
                resource="/ladders/{ladder_id}/players",
                path_params={"ladder_id": "1"},
                method="PUT",
                body="{}"
            ))
        update_player_order_mock.assert_called_once_with(1, False, {})

    def test_update_player_order_with_false_generate_borrowed_points_query_param_should_not_generate_borrowed_points(self):
        with patch.object(self.handler.manager, "update_player_order", return_value=[]) as update_player_order_mock:
            self.handler.handle(create_event(
                resource="/ladders/{ladder_id}/players",
                path_params={"ladder_id": "1"},
                method="PUT",
                query_params={"generate_borrowed_points": "false"},
                body="{}"
            ))
        update_player_order_mock.assert_called_once_with(1, False, {})

    def test_update_player_order_with_true_generate_borrowed_points_query_param_should_generate_borrowed_points(self):
        with patch.object(self.handler.manager, "update_player_order", return_value=[]) as update_player_order_mock:
            self.handler.handle(create_event(
                resource="/ladders/{ladder_id}/players",
                path_params={"ladder_id": "1"},
                method="PUT",
                query_params={"generate_borrowed_points": "true"},
                body="{}"
            ))
        update_player_order_mock.assert_called_once_with(1, True, {})

    def test_update_player(self):
        with patch.object(self.handler.manager, "update_player", return_value={}) as update_player_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/players/{user_id}", {"ladder_id": "1", "user_id": "abc"}, "PUT", "{}"))
        update_player_mock.assert_called_once_with(1, "abc", {})

    def test_get_matches(self):
        with patch.object(self.handler.manager, "get_matches", return_value={}) as get_matches_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/players/{user_id}/matches", {"ladder_id": "1", "user_id": "TEST1"}))
        get_matches_mock.assert_called_once_with(1, "TEST1")

    def test_report_match(self):
        with patch.object(self.handler.manager, "report_match", return_value={}) as report_match_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/matches", {"ladder_id": "1"}, "POST", "{}"))
        report_match_mock.assert_called_once_with(1, {})

    def test_update_match_scores(self):
        with patch.object(self.handler.manager, "update_match_scores", return_value={}) as update_match_scores_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/matches/{match_id}", {"ladder_id": "1", "match_id": "2"}, "PUT", "{}"))
        update_match_scores_mock.assert_called_once_with(2, {})

    def test_delete_match(self):
        with patch.object(self.handler.manager, "delete_match", return_value={}) as delete_match_mock:
            self.handler.handle(create_event("/ladders/{ladder_id}/matches/{match_id}", {"ladder_id": "1", "match_id": "2"}, "DELETE"))
        delete_match_mock.assert_called_once_with(2)


# noinspection PyDefaultArgument
def create_event(resource, path_params=None, method="GET", body=None, query_params=None, headers: Dict[str, str] = {"X-Firebase-Token": ""}):
    event = {
        "resource": resource,
        "httpMethod": method,
        "headers": headers
    }
    if path_params is not None:
        event["pathParameters"] = path_params
    if body is not None:
        event["body"] = body
    if query_params is not None:
        event["queryStringParameters"] = query_params
    return event
