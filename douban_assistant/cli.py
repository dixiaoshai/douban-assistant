from __future__ import annotations

import json
from pathlib import Path

import click

from .douban import (
    DoubanClient,
    DoubanFetchError,
    build_tag_update_plan,
    enrich_book_with_classification,
    load_cookie,
    parse_collect_page,
    subject_id_from_url,
)


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
        enriched = enrich_book_with_classification(book)
        book.intro = enriched.intro
        book.predicted_tags = enriched.predicted_tags
        book.tag_reasons = enriched.tag_reasons
        book.categories = enriched.categories
    click.echo(json.dumps([book.to_dict() for book in books], ensure_ascii=False, indent=2))


@main.command("preview-tag-updates")
@click.option("--user-id", required=True, help="Douban user id from /people/<user_id>/")
@click.option("--max-pages", default=1, show_default=True, type=int, help="Number of pages to fetch.")
@click.option("--cookie", help="Raw Douban Cookie header value.")
@click.option("--cookie-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Path to a text file containing the Douban Cookie header.")
@click.option("--limit", type=int, help="Maximum number of changed books to include in the preview plan.")
@click.option("--book-url", help="Preview a specific Douban book subject URL.")
@click.option("--output", default="data/tag_update_plan.json", show_default=True, type=click.Path(path_type=Path))
def preview_tag_updates_command(
    user_id: str,
    max_pages: int,
    cookie: str | None,
    cookie_file: Path | None,
    limit: int | None,
    book_url: str | None,
    output: Path,
) -> None:
    if not limit and not book_url:
        raise click.ClickException("Use --limit or --book-url for the first safe rollout.")

    client = DoubanClient(cookie=load_cookie(cookie, str(cookie_file) if cookie_file else None))
    try:
        books = client.fetch_books(user_id=user_id, max_pages=max_pages)
        if book_url:
            books = [book for book in books if book.url == book_url]
        enriched_books = []
        for book in books:
            intro = client.fetch_book_intro(book.url)
            enriched_books.append(enrich_book_with_classification(book, intro=intro))
        plan = build_tag_update_plan(enriched_books)
    except DoubanFetchError as exc:
        raise click.ClickException(str(exc)) from exc

    if limit is not None:
        plan = plan[:limit]

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"Saved {len(plan)} tag update candidates to {output}")


@main.command("apply-tag-updates")
@click.option("--plan-file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--cookie", help="Raw Douban Cookie header value.")
@click.option("--cookie-file", type=click.Path(exists=True, dir_okay=False, path_type=Path), help="Path to a text file containing the Douban Cookie header.")
@click.option("--confirm", help="Pass YES to confirm live Douban tag updates.")
@click.option("--limit", type=int, help="Maximum number of selected plan entries to update.")
@click.option("--output", default="data/tag_update_result.json", show_default=True, type=click.Path(path_type=Path))
def apply_tag_updates_command(
    plan_file: Path,
    cookie: str | None,
    cookie_file: Path | None,
    confirm: str | None,
    limit: int | None,
    output: Path,
) -> None:
    if confirm != "YES":
        raise click.ClickException("Pass --confirm YES to apply live Douban tag updates.")

    plan = json.loads(plan_file.read_text(encoding="utf-8"))
    selected = [entry for entry in plan if entry.get("selected", True)]
    if limit is not None:
        selected = selected[:limit]

    client = DoubanClient(cookie=load_cookie(cookie, str(cookie_file) if cookie_file else None))
    results: list[dict] = []
    for entry in selected:
        try:
            payload = client.fetch_interest_editor(entry["subject_id"])
            client.update_book_tags_from_editor_payload(payload, entry.get("suggested_tags", []))
            results.append(
                {
                    "title": entry["title"],
                    "url": entry["url"],
                    "status": "updated",
                    "applied_tags": entry.get("suggested_tags", []),
                }
            )
        except DoubanFetchError as exc:
            results.append(
                {
                    "title": entry["title"],
                    "url": entry["url"],
                    "status": "failed",
                    "error": str(exc),
                }
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    click.echo(f"Processed {len(selected)} tag updates; saved results to {output}")


if __name__ == "__main__":
    main()
