# Douban Tag Writeback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fetch book introductions, generate a reviewable tag update plan, and support confirmed writeback of corrected tags to Douban for a small user-selected subset.

**Architecture:** Extend the existing Douban client with detail-page fetching and authenticated tag update helpers, add introduction-aware tag inference and reasoning output, then expose the workflow through separate preview and apply CLI commands guarded by plan files and explicit confirmation.

**Tech Stack:** Python 3.9+, dataclasses, Click CLI, requests, BeautifulSoup, JSON plan files, unittest-based tests, authenticated Douban session

---

### Task 1: Extend The Data Model For Introduction And Tag Reasoning

**Files:**
- Modify: `douban_assistant/models.py`
- Test: `tests/test_parsing.py`

- [ ] **Step 1: Write the failing test**

```python
def test_parse_collect_page_initializes_intro_and_tag_reason_fields() -> None:
    fixture = Path("tests/fixtures/douban_collect_page_1.html").read_text(encoding="utf-8")
    books = parse_collect_page(fixture)

    assert books[0].intro == ""
    assert books[0].tag_reasons == {}
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_parsing.py::test_parse_collect_page_initializes_intro_and_tag_reason_fields -v`
Expected: FAIL because `BookEntry` does not define `intro` or `tag_reasons`

- [ ] **Step 3: Write minimal implementation**

```python
@dataclass
class BookEntry:
    title: str
    url: str
    authors: list[str] = field(default_factory=list)
    pub_info: str = ""
    date_read: str | None = None
    rating: int | None = None
    douban_tags: list[str] = field(default_factory=list)
    comment: str = ""
    intro: str = ""
    predicted_tags: list[str] = field(default_factory=list)
    tag_reasons: dict[str, list[str]] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_parsing.py::test_parse_collect_page_initializes_intro_and_tag_reason_fields -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/models.py tests/test_parsing.py
git commit -m "feat: add intro and tag reasoning fields"
```

### Task 2: Fetch And Parse Book Introductions

**Files:**
- Modify: `douban_assistant/douban.py`
- Create: `tests/fixtures/douban_book_detail.html`
- Create or modify: `tests/test_book_detail_parsing.py`

- [ ] **Step 1: Write the failing test**

```python
def test_parse_book_detail_extracts_book_intro() -> None:
    html = Path("tests/fixtures/douban_book_detail.html").read_text(encoding="utf-8")

    assert parse_book_intro(html) == "这是一段测试简介。"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_book_detail_parsing.py::test_parse_book_detail_extracts_book_intro -v`
Expected: FAIL because `parse_book_intro` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
def parse_book_intro(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    intro_block = soup.select_one("#link-report .intro")
    if intro_block is None:
        return ""
    return normalize_whitespace(intro_block.get_text(" ", strip=True))


def fetch_book_detail(self, url: str) -> str:
    response = self.session.get(url, timeout=self.timeout)
    response.raise_for_status()
    return response.text
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_book_detail_parsing.py::test_parse_book_detail_extracts_book_intro -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/douban.py tests/fixtures/douban_book_detail.html tests/test_book_detail_parsing.py
git commit -m "feat: parse book introductions from detail pages"
```

### Task 3: Make Tag Inference Introduction-Aware And Explainable

**Files:**
- Modify: `douban_assistant/classifier.py`
- Modify: `tests/test_tagging_rules.py`

- [ ] **Step 1: Write the failing test**

```python
def test_infer_tags_uses_intro_and_records_reasons() -> None:
    book = BookEntry(
        title="测试书",
        url="https://example.com/book",
        intro="这是一本关于帝国、王朝和晚清变局的历史著作。",
    )

    tags, reasons = infer_tags_with_reasons(book)

    assert "历史" in tags
    assert "帝国" in reasons["历史"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_infer_tags_uses_intro_and_records_reasons -v`
Expected: FAIL because the classifier does not return reason traces

- [ ] **Step 3: Write minimal implementation**

```python
def build_haystack(book: BookEntry) -> str:
    return " ".join(
        [
            book.intro,
            book.comment,
            book.title,
            " ".join(book.authors),
            book.pub_info,
            " ".join(book.douban_tags),
        ]
    ).lower()


def infer_tags_with_reasons(book: BookEntry) -> tuple[list[str], dict[str, list[str]]]:
    haystack = build_haystack(book)
    matched: list[str] = []
    reasons: dict[str, list[str]] = {}
    for tag, keywords in TAG_RULES.items():
        hits = [keyword for keyword in keywords if keyword.lower() in haystack]
        if hits:
            matched.append(tag)
            reasons[tag] = hits
    return dedupe_preserving_order(matched), reasons


def infer_tags(book: BookEntry) -> list[str]:
    tags, _ = infer_tags_with_reasons(book)
    return tags
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_infer_tags_uses_intro_and_records_reasons -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/classifier.py tests/test_tagging_rules.py
git commit -m "feat: explain inferred tags with intro-aware reasons"
```

### Task 4: Generate A Reviewable Tag Update Plan

**Files:**
- Modify: `douban_assistant/cli.py`
- Modify: `douban_assistant/douban.py`
- Create: `tests/test_tag_update_plan.py`

- [ ] **Step 1: Write the failing test**

```python
def test_build_tag_update_plan_includes_only_changed_books() -> None:
    books = [
        BookEntry(
            title="A",
            url="https://example.com/a",
            douban_tags=["商业"],
            predicted_tags=["商业"],
            tag_reasons={"商业": ["管理"]},
        ),
        BookEntry(
            title="B",
            url="https://example.com/b",
            douban_tags=[],
            predicted_tags=["历史"],
            tag_reasons={"历史": ["帝国"]},
        ),
    ]

    plan = build_tag_update_plan(books)

    assert len(plan) == 1
    assert plan[0]["title"] == "B"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tag_update_plan.py::test_build_tag_update_plan_includes_only_changed_books -v`
Expected: FAIL because plan generation helpers do not exist

- [ ] **Step 3: Write minimal implementation**

```python
def build_tag_update_plan(books: list[BookEntry]) -> list[dict]:
    plan: list[dict] = []
    for book in books:
        if set(book.douban_tags) == set(book.predicted_tags):
            continue
        plan.append(
            {
                "title": book.title,
                "url": book.url,
                "current_tags": book.douban_tags,
                "suggested_tags": book.predicted_tags,
                "reasons": book.tag_reasons,
                "selected": True,
            }
        )
    return plan
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tag_update_plan.py::test_build_tag_update_plan_includes_only_changed_books -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/cli.py douban_assistant/douban.py tests/test_tag_update_plan.py
git commit -m "feat: generate preview plan for tag updates"
```

### Task 5: Add A Preview CLI For Small-Batch Review

**Files:**
- Modify: `douban_assistant/cli.py`
- Modify: `README.md`
- Modify: `tests/test_client_behavior.py` or create `tests/test_cli_preview.py`

- [ ] **Step 1: Write the failing test**

```python
def test_preview_command_requires_book_limit_or_specific_book() -> None:
    runner = CliRunner()
    result = runner.invoke(main, ["preview-tag-updates", "--user-id", "100654183"])

    assert result.exit_code != 0
    assert "Use --limit or --book-url" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli_preview.py::test_preview_command_requires_book_limit_or_specific_book -v`
Expected: FAIL because the command does not exist

- [ ] **Step 3: Write minimal implementation**

```python
@main.command("preview-tag-updates")
@click.option("--user-id", required=True)
@click.option("--cookie-file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--max-pages", default=1, type=int)
@click.option("--limit", type=int)
@click.option("--book-url")
@click.option("--output", default="data/tag_update_plan.json", type=click.Path(path_type=Path))
def preview_tag_updates_command(...):
    if not limit and not book_url:
        raise click.ClickException("Use --limit or --book-url for the first safe rollout.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli_preview.py::test_preview_command_requires_book_limit_or_specific_book -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/cli.py README.md tests/test_cli_preview.py
git commit -m "feat: add preview command for tag updates"
```

### Task 6: Add Confirmed Writeback Request Construction

**Files:**
- Modify: `douban_assistant/douban.py`
- Create: `tests/test_tag_writeback.py`

- [ ] **Step 1: Write the failing test**

```python
def test_update_book_tags_requires_form_payload() -> None:
    session = FakeSession()
    client = DoubanClient(session=session, cookie="bid=abc")

    client.update_book_tags(
        edit_url="https://book.douban.com/j/subject/1/update",
        tags=["历史", "社会"],
        form_token="token123",
    )

    assert session.last_post_data["tags"] == "历史 社会"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tag_writeback.py::test_update_book_tags_requires_form_payload -v`
Expected: FAIL because writeback helper does not exist

- [ ] **Step 3: Write minimal implementation**

```python
def update_book_tags(self, edit_url: str, tags: list[str], form_token: str) -> None:
    response = self.session.post(
        edit_url,
        data={"tags": " ".join(tags), "ck": form_token},
        timeout=self.timeout,
    )
    response.raise_for_status()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tag_writeback.py::test_update_book_tags_requires_form_payload -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/douban.py tests/test_tag_writeback.py
git commit -m "feat: construct authenticated tag update requests"
```

### Task 7: Add Apply CLI With Explicit Confirmation Gate

**Files:**
- Modify: `douban_assistant/cli.py`
- Modify: `README.md`
- Create or modify: `tests/test_cli_apply.py`

- [ ] **Step 1: Write the failing test**

```python
def test_apply_command_requires_literal_yes_confirmation(tmp_path: Path) -> None:
    plan_file = tmp_path / "plan.json"
    plan_file.write_text("[]", encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(main, ["apply-tag-updates", "--plan-file", str(plan_file)])

    assert result.exit_code != 0
    assert "Pass --confirm YES" in result.output
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_cli_apply.py::test_apply_command_requires_literal_yes_confirmation -v`
Expected: FAIL because the command does not exist

- [ ] **Step 3: Write minimal implementation**

```python
@main.command("apply-tag-updates")
@click.option("--plan-file", required=True, type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--cookie-file", type=click.Path(exists=True, dir_okay=False, path_type=Path))
@click.option("--confirm")
@click.option("--limit", type=int)
def apply_tag_updates_command(...):
    if confirm != "YES":
        raise click.ClickException("Pass --confirm YES to apply live Douban tag updates.")
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_cli_apply.py::test_apply_command_requires_literal_yes_confirmation -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/cli.py README.md tests/test_cli_apply.py
git commit -m "feat: require explicit confirmation for tag writeback"
```

### Task 8: Verify On One Or Two Live Books Only

**Files:**
- Test: `tests/test_book_detail_parsing.py`
- Test: `tests/test_tagging_rules.py`
- Test: `tests/test_tag_update_plan.py`
- Test: `tests/test_tag_writeback.py`
- Manual verification: `data/tag_update_plan.json`
- Manual verification: `data/tag_update_result.json`

- [ ] **Step 1: Run targeted automated tests**

Run: `python3 -m unittest tests.test_cookie_loading tests.test_client_behavior tests.test_tagging_rules -v`
Expected: PASS

- [ ] **Step 2: Run new preview/apply workflow tests**

Run: `python3 -m pytest tests/test_book_detail_parsing.py tests/test_tag_update_plan.py tests/test_tag_writeback.py tests/test_cli_preview.py tests/test_cli_apply.py -v`
Expected: PASS

- [ ] **Step 3: Run live preview for one book**

Run: `python3 -m douban_assistant.cli preview-tag-updates --user-id 100654183 --cookie-file cookie.md --limit 1 --output data/tag_update_plan.json`
Expected: exit 0 and a single-book plan file with current tags, suggested tags, and reasons

- [ ] **Step 4: Run live preview for two books**

Run: `python3 -m douban_assistant.cli preview-tag-updates --user-id 100654183 --cookie-file cookie.md --limit 2 --output data/tag_update_plan.json`
Expected: exit 0 and a two-book plan file

- [ ] **Step 5: Apply one or two confirmed updates**

Run: `python3 -m douban_assistant.cli apply-tag-updates --plan-file data/tag_update_plan.json --cookie-file cookie.md --limit 1 --confirm YES`
Expected: exit 0 and a result file showing one live update attempt

- [ ] **Step 6: Verify on Douban that the tag changed**

Run: manual browser verification on the specific updated book page
Expected: the edited tags match the plan file

- [ ] **Step 7: Commit**

```bash
git add README.md data/tag_update_plan.json data/tag_update_result.json
git commit -m "chore: verify live tag preview and writeback flow"
```
