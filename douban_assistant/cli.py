from __future__ import annotations

import json
from pathlib import Path

import click

from .classifier import classify_book, infer_tags
from .douban import DoubanClient, DoubanFetchError, load_cookie, parse_collect_page


@click.group()
def main() -> None:
    """CLI for the Douban personal assistant."""


@main.command("sync")
@click.option("--user-id", required=True, help="Douban user id from /people/<user_id>/")
@click.option("--max-pages", default=1, show_default=True, type=int, help="Number of pages to fetch.")
@click.option("--output", default="data/books.json", show_default=True, type=click.Path(path_type=Path))
@click.option("--cookie", help="Raw Douban Cookie header value.")
@click.option("--cookie-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Path to a text file containing the Douban Cookie header.")
def sync_command(
    user_id: str,
    max_pages: int,
    output: Path,
    cookie: str | None,
    cookie_file: Path | None,
) -> None:
    client = DoubanClient(cookie=load_cookie(cookie, str(cookie_file) if cookie_file else None))
    try:
        books = client.fetch_books(user_id=user_id, max_pages=max_pages)
    except DoubanFetchError as exc:
        raise click.ClickException(str(exc)) from exc
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps([book.to_dict() for book in books], ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    click.echo(f"Saved {len(books)} books to {output}")


@main.command("check-login")
@click.option("--user-id", required=True, help="Douban user id from /people/<user_id>/")
@click.option("--cookie", help="Raw Douban Cookie header value.")
@click.option("--cookie-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Path to a text file containing the Douban Cookie header.")
def check_login_command(user_id: str, cookie: str | None, cookie_file: Path | None) -> None:
    client = DoubanClient(cookie=load_cookie(cookie, str(cookie_file) if cookie_file else None))
    try:
        books = client.fetch_books(user_id=user_id, max_pages=1)
    except DoubanFetchError as exc:
        raise click.ClickException(str(exc)) from exc

    if books:
        click.echo(f"Access looks good. Parsed {len(books)} books from the first page.")
    else:
        click.echo("Request succeeded, but no books were parsed from the first page.")


@main.command("parse-html")
@click.argument("html_path", type=click.Path(exists=True, path_type=Path))
def parse_html_command(html_path: Path) -> None:
    html = html_path.read_text(encoding="utf-8")
    books = parse_collect_page(html)
    for book in books:
        book.predicted_tags = infer_tags(book)
        book.categories = classify_book(book)
    click.echo(json.dumps([book.to_dict() for book in books], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
