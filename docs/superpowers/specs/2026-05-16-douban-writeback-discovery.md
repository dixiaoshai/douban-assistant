# Douban Writeback Discovery Notes

## Purpose

This note records how the live Douban tag writeback flow was discovered and verified, so future changes do not need to rediscover the same protocol from scratch.

## Starting Point

We already had:

- authenticated collection-page fetches working with `cookie.md`
- local parsing of `读过` books
- local tag inference and classification

What was still unknown:

- where the subject-page introduction text should be extracted from
- how the `修改` action on a collected book actually talks to Douban
- which fields are required to update tags successfully

## Step 1: Confirm The Collection Page Exposes A Modify Entry

We fetched the live collection page for the logged-in user and inspected the HTML around one `subject-item`.

Key finding:

- each collected book includes a `修改` button
- on the collection page this button is rendered as:

```html
<a class="j a_collect_btn" rel="nofollow" name="pbtn-33658616" href="javascript:;">
  修改
</a>
```

This told us:

- the page uses JavaScript to open the edit UI
- there is no direct edit URL in the collection-page markup

## Step 2: Confirm The Subject Page Contains Logged-In Collection State

We fetched a live subject page while authenticated and inspected the logged-in section.

Key findings:

- the page contains a `collect_btn` labeled `修改`
- the page exposes the current collection state, such as `读过`
- the page also exposes a `ck` token in other actions like delete and rating links

Example signals found in the page:

- `id="interest_sect_level"`
- `class="collect_btn"`
- rating links containing `?rating=<n>&ck=-zp3`
- delete form containing `<input type="hidden" name="ck" value="-zp3"/>`

This suggested that:

- `ck` is part of Douban's anti-CSRF protection
- the real update flow probably depends on authenticated session state plus `ck`

## Step 3: Probe Likely Interest Endpoints

Instead of guessing the writeback path, we probed a small set of read-only candidate endpoints with `GET`.

The useful discovery was:

```text
GET https://book.douban.com/j/subject/<subject_id>/interest
```

This endpoint returns JSON and worked while authenticated.

Important result:

- normal guessed paths like `/subject/<id>/interest` returned 404
- the JSON endpoint `/j/subject/<id>/interest` returned 200

## Step 4: Inspect The Interest Editor Payload

The JSON response from:

```text
GET /j/subject/<subject_id>/interest
```

contains:

- `html`
- `tags`
- `my_tags`
- `popular_tags`

The embedded `html` includes the actual edit form:

```html
<form action="https://book.douban.com/j/subject/33658616/interest"
  method="POST"
  class="j a_interest_form book-sns">
```

Important fields found in the form:

- `interest`
- `rating`
- `foldcollect`
- `tags`
- `comment`
- `private`
- `share-shuo`
- submit button `save`

Important observation:

- the current tags are not embedded in the text input value
- instead, the current tags come from the JSON field `tags`

This is why the implementation reads both:

- the JSON wrapper
- the HTML form

## Step 5: Verify Existing State Preservation

We tested the editor payload for books with:

- no tags
- existing tags
- existing comments

Key findings:

- `payload["tags"]` returns the current Douban tags
- the textarea in the form contains the current short comment
- rating and privacy state are present in the form

This mattered because we did not want tag updates to accidentally erase:

- rating
- short comment
- privacy status

## Step 6: First Writeback Attempt Failed With 403

The first direct `POST` to:

```text
POST /j/subject/<subject_id>/interest
```

used the visible form fields but still failed with:

```json
{"r": 1, "code": 403}
```

That told us:

- the visible form fields were not sufficient
- Douban expected additional request context or anti-CSRF data

## Step 7: Rule Out Missing Browser Headers

We retried with minimal browser-like headers:

- `Referer`
- `Origin`
- `X-Requested-With: XMLHttpRequest`

Result:

- still `403`

Conclusion:

- headers alone were not enough

## Step 8: Add The Hidden `ck` Value

From the subject page we already knew Douban uses `ck` in related actions.

Although the interest-editor form HTML did not explicitly include a hidden `ck` field, the authenticated cookie header still contained:

```text
ck=-zp3
```

We retried the same `POST`, this time adding:

```text
ck=<value extracted from cookie>
```

Result:

- response changed from `403` to `200`
- Douban returned success JSON such as:

```json
{
  "r": 0,
  "heading": "收藏成功。写一条广播"
}
```

This was the key breakthrough.

## Final Request Shape

The successful live update used:

```text
POST https://book.douban.com/j/subject/<subject_id>/interest
```

With form data including:

- `interest`
- `rating`
- `foldcollect`
- `ck`
- `tags`
- `comment`
- `save`
- optionally `private`

And request headers including:

- `Referer: https://book.douban.com/subject/<subject_id>/`
- `Origin: https://book.douban.com`
- `X-Requested-With: XMLHttpRequest`

## Safety Decisions Made During Implementation

### 1. Do not broadcast to Douban by default

The form can include `share-shuo`, but the implementation intentionally omits it.

Reason:

- updating tags should not unexpectedly publish a broadcast

### 2. Preserve existing comment/rating/privacy state

The implementation reads current state from the editor form and writes it back with the tag update.

Reason:

- changing tags should not silently clear unrelated collection data

### 3. Require explicit confirmation

The writeback command requires:

```text
--confirm YES
```

Reason:

- all writes are live mutations to Douban data

### 4. Preview before apply

We separated the flow into:

1. `preview-tag-updates`
2. `apply-tag-updates`

Reason:

- this gives the user a reviewable plan file before any mutation

## Introduction Parsing Discovery

For intros, we inspected live subject pages and found the useful content under variants of:

- `#link-report .all .intro`
- `#link-report .intro`
- `.related_info .intro`

The parser now tries these selectors in order and takes the first non-empty result.

## Live Verification Performed

Two real books were used to verify the end-to-end flow:

1. `俄罗斯史（第八版）`
   Applied tags: `历史`, `社会`

2. `悉达多 : 一首印度的诗`
   Applied tag: `诗`

For both books we verified:

- preview file generation
- confirmed apply command execution
- live readback from the Douban interest editor showing updated tags

## Practical Takeaways

- The correct edit endpoint is JSON-based, not a normal page route
- The JSON wrapper plus embedded form HTML both matter
- `ck` is required even when it is not visible in the edit form
- Browser-like headers help keep the request shape consistent
- The safest path is always `preview -> confirm -> apply`
