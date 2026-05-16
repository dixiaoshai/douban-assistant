from pathlib import Path

from douban_assistant.douban import parse_book_intro


def test_parse_book_detail_extracts_book_intro() -> None:
    html = Path("tests/fixtures/douban_book_detail.html").read_text(encoding="utf-8")

    assert parse_book_intro(html) == "这是一段测试简介。"
