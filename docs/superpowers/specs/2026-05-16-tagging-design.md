# Douban Book Tagging Design

## Goal

Read all `读过` books, preserve the original Douban tags, infer corrected or missing tags from currently available fields, and derive project categories from those inferred tags plus existing text.

## Scope

This design only uses data already available from the collection page:

- `title`
- `authors`
- `pub_info`
- `douban_tags`
- `comment`

It does not fetch individual book detail pages or scrape book introductions.

## Data Model

### Existing fields

- `douban_tags`: raw tags captured from Douban collection pages
- `categories`: project-level classification output

### New field

- `predicted_tags`: inferred tags produced by local rules

## Behavior

### 1. Preserve raw Douban data

`douban_tags` remains unchanged in output so the original source data is always recoverable.

### 2. Infer corrected tags

The classifier generates `predicted_tags` from:

- title keywords
- author keywords
- publication info keywords
- existing Douban tags
- short comment keywords

When Douban tags are missing, `predicted_tags` fills the gap.

When Douban tags appear weak or misleading, `predicted_tags` is allowed to differ from them.

### 3. Derive project categories

`categories` is generated from the inferred tag set plus text features. It should reflect the project taxonomy rather than mirror raw Douban tags one-to-one.

## Classification Structure

Use a two-stage classifier:

1. Tag inference layer
   Produces fine-grained tags such as `小说`, `历史`, `心理学`, `商业`, `社会`, `写作`, `技术`

2. Category mapping layer
   Maps inferred tags and text cues to project categories such as `文学`, `历史`, `社会学`, `商业`, `心理学`, `写作表达`, `技术`, `未分类`

## CLI Output

`parse-html` and `sync` should both output:

- raw `douban_tags`
- inferred `predicted_tags`
- derived `categories`

## Error Handling

- If no rules match, `predicted_tags` should be empty or minimal rather than inventing noisy tags
- If no category matches, `categories` should fall back to `未分类`
- Existing network and cookie handling stays unchanged for this feature

## Testing

Add tests covering:

- books without Douban tags get inferred `predicted_tags`
- misleading or sparse Douban tags can be corrected by `predicted_tags`
- `categories` changes based on inferred tags and comments
- sync/parse output includes `predicted_tags`

## Non-Goals

- scraping book detail pages or introductions
- using LLMs or external services
- editing Douban data remotely
