from __future__ import annotations

import unittest

from douban_assistant.douban import build_tag_update_plan
from douban_assistant.models import BookEntry


class TagUpdatePlanTests(unittest.TestCase):
    def test_build_tag_update_plan_includes_only_changed_books(self) -> None:
        books = [
            BookEntry(
                title="A",
                url="https://example.com/a",
                douban_tags=["商业"],
                predicted_tags=["商业"],
                tag_reasons={"商业": ["管理"]},
            ),
            BookEntry(
                title="B",
                url="https://example.com/b",
                douban_tags=[],
                predicted_tags=["历史"],
                tag_reasons={"历史": ["帝国"]},
            ),
        ]

        plan = build_tag_update_plan(books)

        self.assertEqual(len(plan), 1)
        self.assertEqual(plan[0]["title"], "B")

    def test_build_tag_update_plan_skips_books_without_predictions(self) -> None:
        books = [
            BookEntry(
                title="A",
                url="https://example.com/a",
                douban_tags=["哲学"],
                predicted_tags=[],
            )
        ]

        plan = build_tag_update_plan(books)

        self.assertEqual(plan, [])


if __name__ == "__main__":
    unittest.main()
