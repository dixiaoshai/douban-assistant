from __future__ import annotations

import unittest

from douban_assistant.classifier import classify_book, infer_tags
from douban_assistant.models import BookEntry


class TaggingRuleTests(unittest.TestCase):
    def test_infer_tags_uses_comment_and_title_when_douban_tags_missing(self) -> None:
        book = BookEntry(
            title="长安的荔枝",
            url="https://example.com/book",
            authors=["马伯庸"],
            pub_info="马伯庸 / 湖南文艺出版社 / 2022",
            douban_tags=[],
            comment="历史小说，读起来很顺",
        )

        self.assertEqual(infer_tags(book), ["历史", "小说"])

    def test_classify_book_maps_inferred_tags_to_project_categories(self) -> None:
        book = BookEntry(
            title="悉达多",
            url="https://example.com/book",
            authors=["黑塞"],
            pub_info="黑塞 / 天津人民出版社 / 2017",
            douban_tags=[],
            comment="小说里带着很多自我探索",
        )
        book.predicted_tags = infer_tags(book)

        self.assertEqual(classify_book(book), ["文学", "心理学"])

    def test_infer_tags_can_override_sparse_existing_douban_tags(self) -> None:
        book = BookEntry(
            title="俄罗斯史（第八版）",
            url="https://example.com/book",
            authors=["尼古拉·梁赞诺夫斯基"],
            pub_info="上海人民出版社 / 2013",
            douban_tags=["政治"],
            comment="和中国史有些像",
        )

        inferred = infer_tags(book)
        self.assertIn("历史", inferred)
        self.assertNotIn("政治", inferred)


if __name__ == "__main__":
    unittest.main()
