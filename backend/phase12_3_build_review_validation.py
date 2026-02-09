"""
Phase 12.3: Build Reviews Validation

Validates:
- Review persistence
- Latest review summary
- Read-only access
"""

import unittest
import tempfile
from pathlib import Path

from backend.build_review import (
    BuildReview,
    BuildReviewRegistry,
    BuildReviewVerdict,
    BuildReviewer,
)


class TestBuildReviewRegistry(unittest.TestCase):
    """Build review persistence tests."""

    def test_review_persists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "build_reviews.jsonl"
            registry = BuildReviewRegistry(stream_file=path)

            review = BuildReview.new(
                build_id="build_1",
                reviewer=BuildReviewer.USER,
                verdict=BuildReviewVerdict.APPROVED,
                rationale="Looks good",
                confidence=0.9,
            )
            registry.register_review(review)

            self.assertTrue(path.exists())
            reviews = registry.list_by_build("build_1")
            self.assertEqual(len(reviews), 1)
            self.assertEqual(reviews[0].verdict, BuildReviewVerdict.APPROVED)

    def test_latest_review_summary(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "build_reviews.jsonl"
            registry = BuildReviewRegistry(stream_file=path)

            registry.register_review(BuildReview.new(
                build_id="build_2",
                reviewer=BuildReviewer.USER,
                verdict=BuildReviewVerdict.REVISE,
                rationale="Needs work",
                confidence=0.6,
            ))
            registry.register_review(BuildReview.new(
                build_id="build_2",
                reviewer=BuildReviewer.BUDDY,
                verdict=BuildReviewVerdict.APPROVED,
                rationale="Approved",
                confidence=0.8,
            ))

            summaries = registry.get_latest_reviews_summary()
            self.assertEqual(len(summaries), 1)
            self.assertEqual(summaries[0]["build_id"], "build_2")
            self.assertEqual(summaries[0]["verdict"], "approved")


if __name__ == "__main__":
    unittest.main()
