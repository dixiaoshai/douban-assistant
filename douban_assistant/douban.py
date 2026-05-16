from __future__ import annotations

import os
from dataclasses import replace
from typing import Iterable

import requests
from bs4 import BeautifulSoup

from .classifier import classify_book, infer_tags
from .models import BookEntry


BASE_URL = "https://book.douban.com"
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://book.douban.com/",
}


class DoubanFetchError(RuntimeError):
    """Raised when a Douban page cannot be fetched or parsed as expected."""


class DoubanClient:
    def __init__(
        self,
        session: requests.Session | None = None,
        cookie: str | None = None,
        timeout: float = 15.0,
    ) -> None:
        self.session = session or requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        # Ignore shell and system proxy settings unless we explicitly opt in.
        self.session.trust_env = False
        self.timeout = timeout
        cookie = cookie or os.getenv("DOUBAN_COOKIE")
        if cookie:
            self.session.headers["Cookie"] = cookie

    def fetch_collect_page(self, user_id: str, start: int = 0) -> str:
        url = f"{BASE_URL}/people/{user_id}/collect"
        try:
            response = self.session.get(
                url,
                params={"start": start, "sort": "time", "rating": "all"},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.exceptions.RequestException as exc:
            raise DoubanFetchError(f"Failed to fetch Douban page: {exc}") from exc
        html = response.text
        if looks_like_login_page(html):
            raise DoubanFetchError(
                "Douban returned a login page. Add a valid cookie with --cookie-file or DOUBAN_COOKIE."
            )
        if looks_like_permission_error(html):
            raise DoubanFetchError(
                "Douban collection page is not publicly visible to this request. "
                "Use a valid cookie or check the account privacy settings."
            )
        return html

    def fetch_books(self, user_id: str, max_pages: int = 1) -> list[BookEntry]:
        books: list[BookEntry] = []
        for page in range(max_pages):
            html = self.fetch_collect_page(user_id=user_id, start=page * 15)
            page_books = parse_collect_page(html)
            if not page_books:
                break
            books.extend(page_books)
        return [
            replace(
                book,
                predicted_tags=infer_tags(book),
                categories=classify_book(replace(book, predicted_tags=infer_tags(book))),
            )
            for book in books
        ]


def parse_collect_page(html: str) -> list[BookEntry]:
    soup = BeautifulSoup(html, "html.parser")
    items = soup.select(".interest-list .subject-item")
    return [book for item in items if (book := parse_subject_item(item)) is not None]


def parse_subject_item(item) -> BookEntry | None:
    title_link = item.select_one("h2 a")
    if title_link is None:
        return None

    title = normalize_whitespace(title_link.get_text(" ", strip=True))
    url = title_link.get("href", "").strip()

    pub_div = item.select_one(".pub")
    pub_info = normalize_whitespace(pub_div.get_text(" ", strip=True)) if pub_div else ""
    authors = parse_authors(pub_info)

    date_read = None
    rating = None
    date_block = item.select_one(".date")
    if date_block:
        date_read = extract_date(date_block.get_text(" ", strip=True))

    rating_span = item.select_one(".date .rating1-t, .date .rating2-t, .date .rating3-t, .date .rating4-t, .date .rating5-t")
    if rating_span:
        rating = parse_rating_class(rating_span.get("class", []))

    tags = []
    tags_span = item.select_one(".tags")
    if tags_span:
        raw_text = normalize_whitespace(tags_span.get_text(" ", strip=True))
        if ":" in raw_text:
            raw_text = raw_text.split(":", 1)[1]
        tags = [tag.strip() for tag in raw_text.replace("，", ",").split(",") if tag.strip()]

    comment_div = item.select_one(".comment")
    comment = normalize_whitespace(comment_div.get_text(" ", strip=True)) if comment_div else ""

    return BookEntry(
        title=title,
        url=url,
        authors=authors,
        pub_info=pub_info,
        date_read=date_read,
        rating=rating,
        douban_tags=tags,
        comment=comment,
    )


def load_cookie(cookie: str | None = None, cookie_file: str | None = None) -> str | None:
    if cookie:
        return cookie.strip()
    if cookie_file:
        with open(cookie_file, "r", encoding="utf-8") as file:
            content = file.read().strip()
        if "\t" not in content:
            return content

        pairs: list[str] = []
        for line in content.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            key = parts[0].strip()
            value = parts[1].strip()
            if key and value:
                pairs.append(f"{key}={value}")
        if pairs:
            return "; ".join(pairs)
        return content
    return os.getenv("DOUBAN_COOKIE")


def parse_authors(pub_info: str) -> list[str]:
    if not pub_info:
        return []
    parts = [segment.strip() for segment in pub_info.split("/") if segment.strip()]
    if not parts:
        return []
    return parts[:2]


def extract_date(text: str) -> str | None:
    for token in text.split():
        if len(token) == 10 and token[4] == "-" and token[7] == "-":
            return token
    return None


def parse_rating_class(classes: Iterable[str]) -> int | None:
    for class_name in classes:
        if class_name.startswith("rating") and class_name.endswith("-t"):
            value = class_name.removeprefix("rating").removesuffix("-t")
            if value.isdigit():
                return int(value)
    return None


def normalize_whitespace(text: str) -> str:
    return " ".join(text.split())


def looks_like_login_page(html: str) -> bool:
    markers = (
        "登录后查看更多",
        "accounts.douban.com/passport/login",
    )
    return any(marker in html for marker in markers)


def looks_like_permission_error(html: str) -> bool:
    markers = (
        "你没有权限访问这个页面",
        "页面不存在",
        "内容不可见",
        "豆瓣不存在的东西",
    )
    return any(marker in html for marker in markers)
