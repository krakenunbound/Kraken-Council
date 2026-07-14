import unittest

from kouncil_core import (
    BallotValidationError,
    VOTE_CRITERIA,
    bound_attachment_text,
    determine_winner,
    normalize_server_url,
    validate_ballot,
)


def scores(value=8):
    return {criterion: value for criterion in VOTE_CRITERIA}


class BallotTests(unittest.TestCase):
    def test_valid_complete_ballot(self):
        ballot = {"scores": {"C1": scores(8), "C2": scores(6)}}
        self.assertEqual(validate_ballot(ballot, ["C1", "C2"]), {"C1": 40.0, "C2": 30.0})

    def test_rejects_missing_candidate_without_partial_tally(self):
        with self.assertRaises(BallotValidationError):
            validate_ballot({"scores": {"C1": scores()}}, ["C1", "C2"])

    def test_rejects_out_of_range_and_non_numeric_scores(self):
        for bad_value in (0, 11, 999, "10", True, float("nan")):
            with self.subTest(value=bad_value):
                with self.assertRaises(BallotValidationError):
                    validate_ballot({"scores": {"C1": scores(bad_value)}}, ["C1"])

    def test_rejects_missing_criterion(self):
        incomplete = scores()
        incomplete.pop("Accuracy")
        with self.assertRaises(BallotValidationError):
            validate_ballot({"scores": {"C1": incomplete}}, ["C1"])

    def test_unique_winner(self):
        self.assertEqual(determine_winner({"model-a": 90, "model-b": 80}, 2), ("model-a", []))

    def test_tie_is_not_arbitrarily_resolved(self):
        self.assertEqual(
            determine_winner({"model-a": 80, "model-b": 80}, 2),
            (None, ["model-a", "model-b"]),
        )

    def test_no_valid_votes_means_no_winner(self):
        self.assertEqual(determine_winner({"model-a": 0, "model-b": 0}, 0), (None, []))


class ServerUrlTests(unittest.TestCase):
    def test_normalizes_valid_url(self):
        self.assertEqual(normalize_server_url(" http://localhost:11434/ "), "http://localhost:11434")

    def test_rejects_incomplete_or_unsafe_url(self):
        for value in ("localhost:11434", "ftp://localhost", "http://user:pass@localhost", "http://localhost?q=1"):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    normalize_server_url(value)


class AttachmentTests(unittest.TestCase):
    def test_short_text_is_unchanged(self):
        self.assertEqual(bound_attachment_text("hello", 10), "hello")

    def test_long_text_is_marked_and_bounded(self):
        result = bound_attachment_text("x" * 20, 10)
        self.assertTrue(result.startswith("x" * 10))
        self.assertIn("10 characters omitted", result)


if __name__ == "__main__":
    unittest.main()
