import unittest
from datetime import datetime, timedelta

import fixtures
from pytz import timezone
from freezegun import freeze_time
from unittest.mock import patch

from domain import Match, DomainException


class Test(unittest.TestCase):
    # LADDER
    def test_ladder_is_open(self):
        # Test before a ladder is open
        today = datetime.today().date()
        ladder = fixtures.ladder(start_date=today + timedelta(days=1), end_date=today + timedelta(days=2))
        self.assertFalse(ladder.is_open())

        # Test after a ladder is closed
        ladder.start_date = today - timedelta(days=2)
        ladder.end_date = today - timedelta(days=1)
        self.assertFalse(ladder.is_open())

        # Test a valid ladder
        ladder.end_date = today + timedelta(days=1)
        self.assertTrue(ladder.is_open())

    # MATCH

    def test_validate_match(self):
        def assert_error(expected_error_message, match):
            with self.assertRaises(DomainException) as e:
                match.validate()
            self.assertEqual(400, e.exception.status_code)
            self.assertEqual(expected_error_message, e.exception.error_message)

        def create_match(ladder_id, winner_id, loser_id, scores=None):
            w1, l1, w2, l2, w3, l3 = 0, 0, 0, 0, None, None
            if scores is not None:
                w1, l1, w2, l2, w3, l3 = scores
            return Match(None, ladder_id, None, winner_id, loser_id, w1, l1, w2, l2, w3, l3)

        with patch.multiple(Match, is_valid_set=lambda x, y: x != -1 and y != -1, is_valid_tiebreak=lambda x, y: x != -2 and y != -2):
            # Test match with no ladder id
            assert_error("Missing ladder_id", create_match(None, None, None))

            # Test match with null winner id
            assert_error("Missing winner's user_id", create_match(0, None, 1))

            # Test match with null loser id
            assert_error("Missing loser's user_id", create_match(0, 1, None))

            # Test match against oneself
            assert_error("A match cannot be played against oneself", create_match(0, 1, 1))

            # Test invalid first set
            assert_error("Invalid scores for set 1", create_match(0, 1, 2, [-1, -1, 0, 0, None, None]))

            # Test invalid second set
            assert_error("Invalid scores for set 2", create_match(0, 1, 2, [0, 0, -1, -1, None, None]))

            # Test invalid third set
            assert_error("Invalid scores for set 3", create_match(0, 1, 2, [0, 0, 0, 0, -1, -2]))

            # Test winning all three sets
            assert_error("Invalid scores. This is a best 2 out of 3 set format. One player cannot win all three sets.", create_match(0, 1, 2, [1, 0, 1, 0, 1, 0]))

            # Test loser reporting score
            assert_error("Invalid scores. Only winners report the scores. Please contact the winner for your scores to be reported.", create_match(0, 1, 2, [0, 1, 0, 1, None, None]))
            assert_error("Invalid scores. Only winners report the scores. Please contact the winner for your scores to be reported.", create_match(0, 1, 2, [0, 1, 1, 0, 0, 1]))

            # Test no third set
            create_match(0, 1, 2, [1, 0, 1, 0, None, None]).validate()

            # Test valid third set
            create_match(0, 1, 2, [1, 0, 0, 1, 1, -2]).validate()

            # Test valid third tiebreak
            create_match(0, 1, 2, [1, 0, 0, 1, 1, -1]).validate()

    def test_played_today(self):
        test_date = datetime(2019, 1, 1, tzinfo=timezone("US/Mountain"))
        test_match = Match(None, None, test_date, None, None, None, None, None, None)

        # Test exact same time (beginning of today)
        with freeze_time(test_date):
            self.assertTrue(test_match.played_today())

        # Test last second of today (end of today)
        with freeze_time(test_date + timedelta(days=1) - timedelta(seconds=1)):
            self.assertTrue(test_match.played_today())

        # Test one second before (end of previous day)
        with freeze_time(test_date - timedelta(seconds=1)):
            self.assertFalse(test_match.played_today())

        # Test one day after (beginning of next day)
        with freeze_time(test_date + timedelta(days=1)):
            self.assertFalse(test_match.played_today())

    def test_has_players(self):
        def create_match(winner_id, loser_id):
            return Match(None, None, None, winner_id, loser_id, None, None, None, None)

        self.assertTrue(create_match("TEST0", "TEST1").has_players("TEST0"))
        self.assertTrue(create_match("TEST0", "TEST1").has_players("TEST1"))
        self.assertFalse(create_match("TEST0", "TEST1").has_players("TEST2"))
        self.assertTrue(create_match("TEST0", "TEST1").has_players("TEST0", "TEST1"))
        self.assertTrue(create_match("TEST0", "TEST1").has_players("TEST1", "TEST0"))
        self.assertFalse(create_match("TEST0", "TEST1").has_players("TEST0", "TEST2"))
        self.assertFalse(create_match("TEST0", "TEST1").has_players("TEST2", "TEST1"))
        self.assertFalse(create_match("TEST0", "TEST1").has_players("TEST2", "TEST3"))

    def test_is_valid_set(self):
        self.assertFalse(Match.is_valid_set(None, None))
        self.assertFalse(Match.is_valid_set(0, 0))
        self.assertFalse(Match.is_valid_set(2, 1))
        self.assertFalse(Match.is_valid_set(10, 0))
        self.assertFalse(Match.is_valid_set(6, 6))
        self.assertFalse(Match.is_valid_set(5, 6))
        self.assertFalse(Match.is_valid_set(7, 4))
        self.assertFalse(Match.is_valid_set(7, 7))
        self.assertFalse(Match.is_valid_set(6, -1))
        self.assertTrue(Match.is_valid_set(0, 6))
        self.assertTrue(Match.is_valid_set(6, 0))
        self.assertTrue(Match.is_valid_set(4, 6))
        self.assertTrue(Match.is_valid_set(6, 4))
        self.assertTrue(Match.is_valid_set(7, 5))
        self.assertTrue(Match.is_valid_set(5, 7))
        self.assertTrue(Match.is_valid_set(6, 7))
        self.assertTrue(Match.is_valid_set(7, 6))

    def test_is_valid_tiebreak(self):
        self.assertFalse(Match.is_valid_tiebreak(None, None))
        self.assertFalse(Match.is_valid_tiebreak(0, 0))
        self.assertFalse(Match.is_valid_tiebreak(6, 1))
        self.assertFalse(Match.is_valid_tiebreak(7, 9))
        self.assertFalse(Match.is_valid_tiebreak(10, 10))
        self.assertFalse(Match.is_valid_tiebreak(10, 9))
        self.assertFalse(Match.is_valid_tiebreak(8, 11))
        self.assertFalse(Match.is_valid_tiebreak(10, -1))
        self.assertFalse(Match.is_valid_tiebreak(0, 10))
        self.assertTrue(Match.is_valid_tiebreak(10, 0))
        self.assertTrue(Match.is_valid_tiebreak(10, 8))
        self.assertTrue(Match.is_valid_tiebreak(11, 9))
        self.assertTrue(Match.is_valid_tiebreak(150, 148))

    def test_calculate_scores(self):
        def assert_success(match, new_winner_score, new_loser_score):
            winner_score, loser_score = match.calculate_scores(0, 0, False)
            self.assertEqual(new_winner_score, winner_score)
            self.assertEqual(new_loser_score, loser_score)

        def create_match(w1, l1, w2, l2, w3=None, l3=None):
            return Match(None, None, None, None, None, w1, l1, w2, l2, w3, l3)

        with patch.object(Match, "calculate_distance_points", return_value=0):
            # Test valid matches
            assert_success(create_match(6, 0, 6, 0), 39, 0)
            assert_success(create_match(6, 0, 6, 0), 39, 0)
            assert_success(create_match(6, 1, 6, 0), 38, 1)
            assert_success(create_match(6, 3, 6, 3), 33, 6)
            assert_success(create_match(7, 5, 6, 3), 31, 8)

            # Third sets
            assert_success(create_match(6, 0, 0, 6, 6, 0), 33, 6)
            assert_success(create_match(0, 6, 6, 0, 6, 0), 33, 6)
            assert_success(create_match(7, 6, 6, 7, 7, 6), 20, 19)

            # Tiebreaks
            with patch.object(Match, "played_tiebreak", return_value=True):
                assert_success(create_match(6, 0, 0, 6, 10, 8), 29, 10)
                assert_success(create_match(6, 0, 0, 6, 10, 7), 29, 10)
                assert_success(create_match(6, 0, 0, 6, 15, 13), 27, 12)
                assert_success(create_match(6, 0, 0, 6, 200, 198), 27, 12)
                assert_success(create_match(7, 6, 6, 7, 200, 198), 20, 19)

        # Pretend that there is distance penalty of 5
        with patch.object(Match, "calculate_distance_points", return_value=-5):
            assert_success(create_match(6, 0, 6, 0), 34, 0)
            assert_success(create_match(7, 6, 6, 7, 7, 6), 15, 19)

        # Pretend that there is a distance premium of 10
        with patch.object(Match, "calculate_distance_points", return_value=10):
            assert_success(create_match(6, 0, 6, 0), 49, 0)
            assert_success(create_match(7, 6, 6, 7, 7, 6), 30, 19)

        # Test that with a large penalty, the winner's score cannot go below 12
        with patch.object(Match, "calculate_distance_points", return_value=-100):
            assert_success(create_match(7, 6, 6, 7, 7, 6), 12, 19)

    def test_played_tiebreak(self):
        def match_played_tiebreak(winner_set3_score, loser_set3_score):
            return Match(None, None, None, None, None, None, None, None, None, winner_set3_score, loser_set3_score).played_tiebreak()

        # Test no third set
        self.assertFalse(match_played_tiebreak(None, None))

        # Test valid sets
        self.assertFalse(match_played_tiebreak(6, 0))
        self.assertFalse(match_played_tiebreak(6, 4))
        self.assertFalse(match_played_tiebreak(7, 5))
        self.assertFalse(match_played_tiebreak(7, 6))

        # Test valid tiebreaks
        self.assertTrue(match_played_tiebreak(10, 0))
        self.assertTrue(match_played_tiebreak(10, 8))
        self.assertTrue(match_played_tiebreak(11, 9))
        self.assertTrue(match_played_tiebreak(200, 198))

    def test_calculate_distance_penalty(self):
        # Test when distance penalty is off
        self.assertEqual(0, Match.calculate_distance_points(1, 2, False))

        # Test penalties
        self.assertEqual(-2, Match.calculate_distance_points(1, 2, True))
        self.assertEqual(-8, Match.calculate_distance_points(1, 5, True))
        self.assertEqual(-8, Match.calculate_distance_points(7, 11, True))
        self.assertEqual(-10, Match.calculate_distance_points(1, 6, True))

        # Test premiums
        self.assertEqual(3, Match.calculate_distance_points(2, 1, True))
        self.assertEqual(12, Match.calculate_distance_points(5, 1, True))
        self.assertEqual(12, Match.calculate_distance_points(11, 7, True))
        self.assertEqual(15, Match.calculate_distance_points(6, 1, True))
