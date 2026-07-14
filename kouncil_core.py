"""Pure, offline-testable decision helpers for Kraken Kouncil."""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from urllib.parse import urlparse


VOTE_CRITERIA = (
    "Relevance",
    "Clarity",
    "Completeness",
    "Accuracy",
    "Helpfulness",
)


class BallotValidationError(ValueError):
    """Raised when a model returns an incomplete or unsafe ballot."""


def normalize_server_url(value: str) -> str:
    """Validate and normalize an HTTP(S) local-model server URL."""
    normalized = value.strip().rstrip("/")
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("enter a complete http:// or https:// server URL")
    if parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ValueError("credentials, query strings, and fragments are not allowed in server URLs")
    return normalized


def bound_attachment_text(text: str, limit: int = 100_000) -> str:
    """Limit prompt attachment text while clearly marking truncation."""
    if len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n\n[Attachment truncated: {omitted:,} characters omitted]"


def validate_ballot(ballot: object, candidates: Sequence[str]) -> dict[str, float]:
    """Validate a complete ballot and return candidate totals without side effects."""
    if not isinstance(ballot, Mapping):
        raise BallotValidationError("ballot must be a JSON object")
    scores = ballot.get("scores")
    if not isinstance(scores, Mapping):
        raise BallotValidationError("ballot.scores must be a JSON object")

    expected = set(candidates)
    received = set(scores)
    if received != expected:
        missing = sorted(expected - received)
        extra = sorted(received - expected)
        raise BallotValidationError(f"candidate mismatch; missing={missing}, extra={extra}")

    totals: dict[str, float] = {}
    for candidate in candidates:
        candidate_scores = scores[candidate]
        if not isinstance(candidate_scores, Mapping):
            raise BallotValidationError(f"scores for {candidate} must be an object")
        if set(candidate_scores) != set(VOTE_CRITERIA):
            raise BallotValidationError(f"criteria mismatch for {candidate}")

        total = 0.0
        for criterion in VOTE_CRITERIA:
            value = candidate_scores[criterion]
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise BallotValidationError(f"{candidate}.{criterion} must be numeric")
            numeric = float(value)
            if not math.isfinite(numeric) or not 1 <= numeric <= 10:
                raise BallotValidationError(f"{candidate}.{criterion} must be between 1 and 10")
            total += numeric
        totals[candidate] = total
    return totals


def determine_winner(
    tally: Mapping[str, float], valid_vote_count: int
) -> tuple[str | None, list[str]]:
    """Return a unique winner, or no winner plus tied candidates."""
    if valid_vote_count < 1 or not tally:
        return None, []
    highest = max(tally.values())
    tied = [candidate for candidate, score in tally.items() if score == highest]
    if len(tied) != 1:
        return None, tied
    return tied[0], []
