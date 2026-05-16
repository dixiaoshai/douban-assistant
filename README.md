# Douban Personal Assistant

This project starts with one focused job: read the books marked as `读过` on a Douban account and classify them automatically.

## MVP scope

- Fetch books from a Douban public `读过` page
- Parse title, author, rating, dates, tags, and short comment
- Classify books with deterministic rules
- Export the result as JSON

## Current approach

The first version uses public Douban book collection pages such as:

`https://book.douban.com/people/<douban_id>/collect`

That keeps the MVP simple and avoids relying on private or brittle unofficial APIs. If your collection page is private, the next step would be adding cookie-based authenticated fetching.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Usage

```bash
douban-assistant sync \
  --user-id your_douban_id \
  --max-pages 3 \
  --output data/books.json
```

If the page is private, add your Douban cookie:

```bash
douban-assistant check-login \
  --user-id your_douban_id \
  --cookie-file secrets/douban_cookie.txt

douban-assistant sync \
  --user-id your_douban_id \
  --max-pages 3 \
  --cookie-file secrets/douban_cookie.txt \
  --output data/books.json
```

`--cookie-file` accepts either:

- a raw `Cookie` header value such as `bid=...; dbcl2="..."; ck=...`
- a browser-exported tab-separated cookie table where the first two columns are the cookie key and value

That means a file like `cookie.md` can be used directly as long as each line starts with `key<TAB>value`.

You can also set `DOUBAN_COOKIE` as an environment variable instead of using `--cookie-file`.

You can also parse saved HTML locally while developing:

```bash
douban-assistant parse-html tests/fixtures/douban_collect_page_1.html
```

## Classification strategy

The built-in classifier uses simple transparent rules:

- Douban tags
- Title keywords
- Author keywords
- Rating and review metadata

Example categories:

- `文学`
- `历史`
- `社会学`
- `商业`
- `心理学`
- `写作表达`
- `技术`
- `未分类`

This is intentionally easy to inspect. Later we can add:

1. a personal taxonomy
2. AI-assisted relabeling
3. semantic clustering across the whole reading list

## Notes

- Douban page structure can change, so selectors may need small updates over time.
- Please only fetch your own or publicly visible pages and keep request frequency low.
- Keep your cookie file out of git. A local `secrets/` directory is a good default.
