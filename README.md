# Douban Personal Assistant

This project starts with one focused job: read the books marked as `读过` on a Douban account, infer a best-fit tag from the available metadata, and safely prepare tag updates for review before any live writeback.

## Current scope

- Fetch books from a Douban public `读过` page
- Parse title, author, rating, dates, tags, and short comment
- Fetch book detail-page introductions when needed
- Infer one most-likely tag with deterministic rules
- Derive internal categories from that inferred tag
- Preview proposed tag changes before any live update
- Apply confirmed tag changes back to Douban
- Export the result as JSON

## Current approach

The first version uses public Douban book collection pages such as:

`https://book.douban.com/people/<douban_id>/collect`

That keeps the collection-page parsing simple. For private pages, detail-page intros, and live tag writeback, the tool uses your authenticated Douban cookie.

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

The parsed output now includes:

- `douban_tags`: original tags currently stored on Douban
- `intro`: fetched introduction text when available
- `predicted_tags`: one best-fit predicted tag
- `tag_reasons`: matched keywords that explain the prediction
- `categories`: internal project categories derived from the predicted tag

## Preview and apply tag updates

To improve tag recommendations with book introductions and review updates before writing anything back to Douban:

```bash
douban-assistant preview-tag-updates \
  --user-id your_douban_id \
  --cookie-file cookie.md \
  --book-url https://book.douban.com/subject/25748806/ \
  --output data/tag_update_plan.json
```

How preview works:

- the tool fetches the current collection list
- for each candidate book it fetches the subject-page introduction
- it predicts one most-likely tag from title, intro, comment, and other metadata
- books without any predicted tag are skipped, which means their original Douban tags stay unchanged
- the preview output only includes books whose current tags differ from the predicted tag

For the first safe rollout, use `--book-url` or `--limit` so you only inspect one or two books at a time.

Recommended workflow:

1. Generate `data/tag_update_plan.json`
2. Review the proposed `current_tags -> suggested_tags` changes
3. Apply only after you are comfortable with the plan

After reviewing the generated plan file, apply the selected updates with an explicit confirmation gate:

```bash
douban-assistant apply-tag-updates \
  --plan-file data/tag_update_plan.json \
  --cookie-file cookie.md \
  --limit 1 \
  --confirm YES \
  --output data/tag_update_result.json
```

The apply command updates Douban live, so review the plan file carefully before using `--confirm YES`.

During apply, the tool:

- preserves existing rating, short comment, and privacy state
- does not post a Douban broadcast by default
- sends the authenticated `ck` token required by Douban's interest editor
- writes a local result file so you can verify which books were updated

For a cautious rollout, apply one or two updates first:

```bash
douban-assistant apply-tag-updates \
  --plan-file data/tag_update_plan.json \
  --cookie-file cookie.md \
  --limit 1 \
  --confirm YES \
  --output data/tag_update_result.json
```

## Classification strategy

The built-in classifier uses simple transparent rules and keeps them explainable.

Input sources:

- Title keywords
- Introduction keywords
- Short comment keywords
- Author and publication metadata
- Existing Douban tags as weak hints

Prediction rule:

- only one most-likely tag is kept in `predicted_tags`
- if no confident tag is predicted, the book is skipped in the update plan and its original Douban tags remain untouched

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
- Please only fetch your own or publicly visible pages, keep request frequency low, and batch write updates carefully.
- Keep your cookie file out of git. A local `secrets/` directory is a good default.
- If Douban temporarily returns `403`, wait a bit and retry with a smaller batch.
