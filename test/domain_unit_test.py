import unittest

from domain import Match, DomainException

class Test(unittest.TestCase):
    def test_validate_match(self):
        def assert_error(expected_error_message, match):
            with self.assertRaises(DomainException) as e:
                match.validate()
            self.assertEqual(DomainException.MESSAGE_FORMAT.format(expected_error_message), e.exception.error_message)

        # Test match with no ladder id
        assert_error("Missing ladder_id", Match(None, None, "2018-01-01", 1, 2, 6, 0, 6, 0))

        # Test match with no date
        assert_error("Missing match_date", Match(None, 0, None, 1, 2, 6, 0, 6, 0))

        # Test match with null winner id
        assert_error("Missing winner_id", Match(None, 0, "2018-01-01", None, 1, 6, 0, 6, 0))

        # Test match with null loser id
        assert_error("Missing loser_id", Match(None, 0, "2018-01-01", 1, None, 6, 0, 6, 0))

        # Test match against oneself
        assert_error("A match cannot be played against oneself", Match(None, 0, "2018-01-01", 1, 1, 6, 0, 6, 0))

    def _test_is_valid_set(self):
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

    def _test_is_valid_tiebreak(self):
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

    def _test_calculate_score(self):
        def assert_success(match, new_winner_score, new_loser_score):
            winner_score, loser_score = match.calculate_scores()
            self.assertEqual(new_winner_score, winner_score)
            self.assertEqual(new_loser_score, loser_score)

        def create_match(w1, l1, w2, l2, w3 = None, l3 = None):
            return Match(None, None, None, w1, l1, w2, l2, w3, l3)

        # Temporarily overwrite the calculate_distance_penalty function for easier testing
        old_function = Match.calculate_distance_penalty
        Match.calculate_distance_penalty = lambda winner_rank, loser_rank: 0

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
        assert_success(create_match(6, 0, 0, 6, 10, 8), 29, 10)
        assert_success(create_match(6, 0, 0, 6, 10, 7), 29, 10)
        assert_success(create_match(6, 0, 0, 6, 16, 14), 20, 19)
        assert_success(create_match(6, 0, 0, 6, 200, 198), 20, 19)

        # Pretend that there is distance penalty of -10
        Match.calculate_distance_penalty = lambda winner_rank, loser_rank: -10
        assert_success(create_match(6, 0, 6, 0), 29, 0)
        assert_success(create_match(7, 6, 6, 7, 7, 6), 10, 19)

        # Pretend that there is a distance penalty of 10
        Match.calculate_distance_penalty = lambda winner_rank, loser_rank: 10
        assert_success(create_match(6, 0, 6, 0), 49, 0)
        assert_success(create_match(7, 6, 6, 7, 7, 6), 30, 19)

        # Reset the function to the real one (so that other tests can run)
        Match.calculate_distance_penalty = old_function

    def _test_calculate_distance_penalty(self):
        # Test zero-tier penalty
        self.assertEqual(0, Match.calculate_distance_penalty(1, 2))
        self.assertEqual(0, Match.calculate_distance_penalty(1, 5))
        self.assertEqual(0, Match.calculate_distance_penalty(7, 11))

        # Test zero-tier premium
        self.assertEqual(0, Match.calculate_distance_penalty(2, 1))
        self.assertEqual(0, Match.calculate_distance_penalty(5, 1))
        self.assertEqual(0, Match.calculate_distance_penalty(11, 7))

        # Test first-tier penalty
        self.assertEqual(-3, Match.calculate_distance_penalty(1, 6))
        self.assertEqual(-6, Match.calculate_distance_penalty(1, 7))
        self.assertEqual(-9, Match.calculate_distance_penalty(1, 8))
        self.assertEqual(-12, Match.calculate_distance_penalty(1, 9))

        # Test first-tier premium
        self.assertEqual(3, Match.calculate_distance_penalty(6, 1))
        self.assertEqual(6, Match.calculate_distance_penalty(7, 1))
        self.assertEqual(9, Match.calculate_distance_penalty(8, 1))
        self.assertEqual(12, Match.calculate_distance_penalty(9, 1))

        # Test second-tier penalty
        self.assertEqual(-16, Match.calculate_distance_penalty(1, 10))
        self.assertEqual(-20, Match.calculate_distance_penalty(1, 11))
        self.assertEqual(-24, Match.calculate_distance_penalty(1, 12))
        self.assertEqual(-28, Match.calculate_distance_penalty(1, 13))

        # Test first-tier premium
        self.assertEqual(15, Match.calculate_distance_penalty(10, 1))
        self.assertEqual(18, Match.calculate_distance_penalty(11, 1))
        self.assertEqual(21, Match.calculate_distance_penalty(12, 1))
        self.assertEqual(24, Match.calculate_distance_penalty(13, 1))
