from pathlib import Path

from douban_assistant.douban import (
    looks_like_login_page,
    looks_like_permission_error,
    load_cookie,
)


def test_load_cookie_prefers_inline_value() -> None:
    assert load_cookie(cookie="abc=123", cookie_file=None) == "abc=123"


def test_load_cookie_reads_raw_cookie_header_file(tmp_path: Path) -> None:
    cookie_file = tmp_path / "douban_cookie.txt"
    cookie_file.write_text('bid=abc; dbcl2="123:xyz"', encoding="utf-8")

    assert load_cookie(cookie=None, cookie_file=str(cookie_file)) == 'bid=abc; dbcl2="123:xyz"'


def test_load_cookie_reads_tabular_cookie_export_file(tmp_path: Path) -> None:
    cookie_file = tmp_path / "cookie.md"
    cookie_file.write_text(
        'bid\tabc\t.douban.com\t/\n'
        'dbcl2\t"123:xyz"\t.douban.com\t/\n',
        encoding="utf-8",
    )

    assert load_cookie(cookie=None, cookie_file=str(cookie_file)) == 'bid=abc; dbcl2="123:xyz"'


def test_detect_login_page_markers() -> None:
    html = "<html><body>登录后查看更多，打开豆瓣</body></html>"
    assert looks_like_login_page(html) is True


def test_detect_permission_error_markers() -> None:
    html = "<html><body>你没有权限访问这个页面</body></html>"
    assert looks_like_permission_error(html) is True
