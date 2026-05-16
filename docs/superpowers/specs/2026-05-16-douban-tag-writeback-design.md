# Douban Tag Writeback Design

## Goal

Fetch book detail-page introductions to improve tag inference, then support writing corrected tags back to Douban through a guarded `preview -> confirm -> apply` workflow.

## Scope

This feature adds two capabilities:

1. Fetch and use book introductions from each book detail page
2. Write updated tags back to Douban, but only after explicit user confirmation

The first implementation should be tested on one or two books before wider rollout.

## Safety Model

Writing to Douban is a real data mutation, so the workflow must make accidental writes difficult.

### Required flow

1. Generate a preview plan locally
2. Show the current tags and recommended tags for each candidate book
3. Let the user review the plan file
4. Require an explicit confirmation step before any write
5. Apply only the confirmed entries

### Confirmation gate

The apply command should require the user to pass a confirmation flag or type a literal confirmation string such as `YES`.

No preview file means no writeback.

## Data Sources

### Collection page fields

- title
- authors
- pub_info
- douban_tags
- comment
- book URL

### Detail page fields

- book introduction text when available
- optional editor or author introduction if clearly separable

The first version should prioritize the book introduction text only.

## Data Model Changes

### Extend book data

Add fields that keep the classification trace explicit:

- `intro`: fetched introduction text
- `predicted_tags`: inferred tags from title, comment, existing tags, and introduction
- `tag_reasons`: short reasons or keyword hits that explain why each predicted tag was chosen

### Writeback plan entry

Represent each proposed update as a structured object containing:

- title
- book URL
- current Douban tags
- suggested tags
- reasons
- whether it is selected for apply

## Classification Behavior

### Tag inference

Use the existing local rule system as the base, then enrich it with introduction text.

Priority order:

1. introduction text
2. short comment
3. title
4. authors and publication info
5. existing Douban tags as weak hints only

Existing Douban tags should not dominate when the introduction strongly suggests a better label.

### Traceability

The preview output should explain the recommendation in compact text, for example:

- `历史`: hit `俄罗斯史`, `帝国`
- `商业`: hit `组织`, `管理`

## CLI Design

### 1. Preview command

Add a command that:

- fetches the current collection list
- fetches introductions for candidate books
- recomputes `predicted_tags`
- compares them against current Douban tags
- writes a review file such as `data/tag_update_plan.json`

Suggested options:

- `--user-id`
- `--cookie-file`
- `--max-pages`
- `--limit`
- `--book-url`
- `--output`

`--limit` and `--book-url` are important for the first safe rollout on one or two books.

### 2. Apply command

Add a second command that:

- reads the preview plan file
- verifies confirmation input
- submits tag updates to Douban
- records per-book success or failure

Suggested options:

- `--plan-file`
- `--cookie-file`
- `--confirm`
- `--limit`

## Writeback Mechanics

The implementation should inspect the book collection edit flow and reuse the same authenticated session.

The writeback logic must:

- fetch the edit form if needed
- capture any anti-CSRF token or hidden form fields required by Douban
- submit the updated tags in the format Douban expects
- detect whether the update succeeded

Because this touches live user data, the first version should update only a small explicitly selected subset.

## Rate Limiting And Reliability

Use conservative request pacing during writeback.

Requirements:

- sleep between write requests
- stop or continue safely on per-book failure
- save a result log file such as `data/tag_update_result.json`

## Initial Rollout

The first live verification should target one or two books only.

Recommended progression:

1. run preview on one or two specific books
2. inspect the recommended tags and reasons
3. run apply on those same books with confirmation
4. verify on Douban that the tags changed as expected
5. only then consider larger batches

## Testing

Add tests for:

- introduction parsing from saved detail-page fixtures
- introduction-aware tag inference
- preview plan generation
- confirmation gate enforcement
- writeback request construction using a fake session

Manual verification must cover:

- one-book preview
- one-book writeback
- two-book writeback

## Non-Goals

- fully automatic bulk writeback without review
- LLM-based classification
- editing ratings, comments, or reading dates
