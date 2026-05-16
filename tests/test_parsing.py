from pathlib import Path

from douban_assistant.classifier import classify_book, infer_tags
from douban_assistant.douban import parse_collect_page


def test_parse_collect_page_extracts_books() -> None:
    fixture = Path("tests/fixtures/douban_collect_page_1.html").read_text(encoding="utf-8")
    books = parse_collect_page(fixture)

    assert len(books) == 2
    assert books[0].title == "置身事内"
    assert books[0].authors == ["兰小欢", "上海人民出版社"]
    assert books[0].date_read == "2025-03-01"
    assert books[0].rating == 4
    assert books[0].douban_tags == ["经济", "商业", "中国"]
    assert books[0].predicted_tags == []
    assert books[0].intro == ""
    assert books[0].tag_reasons == {}


def test_classify_book_uses_keywords() -> None:
    fixture = Path("tests/fixtures/douban_collect_page_1.html").read_text(encoding="utf-8")
    books = parse_collect_page(fixture)

    books[0].predicted_tags = infer_tags(books[0])
    books[1].predicted_tags = infer_tags(books[1])
    first_categories = classify_book(books[0])
    second_categories = classify_book(books[1])

    assert "商业" in first_categories
    assert "心理学" in second_categories
