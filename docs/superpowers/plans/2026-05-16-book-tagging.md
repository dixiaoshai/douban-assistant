# Book Tagging Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Preserve raw Douban tags, infer corrected or missing tags from current collection-page data, and derive project categories from those inferred tags.

**Architecture:** Extend the `BookEntry` model with a `predicted_tags` field, split classification into tag inference and category mapping, and keep raw `douban_tags` untouched in parsing and export. The CLI continues to fetch and serialize books, but now writes both inferred tags and derived categories.

**Tech Stack:** Python 3.9+, dataclasses, Click CLI, requests, BeautifulSoup, unittest/pytest-style existing tests

---

### Task 1: Add The New Output Field

**Files:**
- Modify: `douban_assistant/models.py`
- Test: `tests/test_parsing.py`

- [ ] **Step 1: Write the failing test**

```python
def test_parse_collect_page_initializes_predicted_tags() -> None:
    fixture = Path("tests/fixtures/douban_collect_page_1.html").read_text(encoding="utf-8")
    books = parse_collect_page(fixture)

    assert books[0].predicted_tags == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_parsing.py::test_parse_collect_page_initializes_predicted_tags -v`
Expected: FAIL with `AttributeError` or missing field assertion for `predicted_tags`

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
    predicted_tags: list[str] = field(default_factory=list)
    categories: list[str] = field(default_factory=list)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_parsing.py::test_parse_collect_page_initializes_predicted_tags -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/models.py tests/test_parsing.py
git commit -m "feat: add predicted tag field"
```

### Task 2: Introduce Tag Inference Rules

**Files:**
- Modify: `douban_assistant/classifier.py`
- Create or modify: `tests/test_tagging_rules.py`

- [ ] **Step 1: Write the failing test**

```python
def test_infer_tags_uses_comment_and_title_when_douban_tags_missing() -> None:
    book = BookEntry(
        title="长安的荔枝",
        url="https://example.com/book",
        authors=["马伯庸"],
        pub_info="马伯庸 / 湖南文艺出版社 / 2022",
        douban_tags=[],
        comment="历史小说，读起来很顺",
    )

    assert infer_tags(book) == ["历史", "小说"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_infer_tags_uses_comment_and_title_when_douban_tags_missing -v`
Expected: FAIL because `infer_tags` does not exist

- [ ] **Step 3: Write minimal implementation**

```python
TAG_RULES: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        ("历史", ("历史", "中国史", "世界史", "帝国", "王朝", "晚清")),
        ("小说", ("小说", "虚构", "短篇")),
        ("散文", ("散文", "随笔")),
        ("心理学", ("心理", "情绪", "关系", "认知", "人格")),
        ("商业", ("商业", "品牌", "营销", "管理", "创业", "投资")),
        ("社会", ("社会", "阶层", "性别", "传播", "人类学")),
        ("写作", ("写作", "表达", "沟通", "采访", "叙事", "文案")),
        ("技术", ("计算机", "互联网", "编程", "算法", "人工智能", "AI", "产品")),
    ]
)


def infer_tags(book: BookEntry) -> list[str]:
    haystack = build_haystack(book)
    matched: list[str] = []
    for tag, keywords in TAG_RULES.items():
        if any(keyword.lower() in haystack for keyword in keywords):
            matched.append(tag)
    return matched
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_infer_tags_uses_comment_and_title_when_douban_tags_missing -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/classifier.py tests/test_tagging_rules.py
git commit -m "feat: infer tags from collection metadata"
```

### Task 3: Map Inferred Tags To Project Categories

**Files:**
- Modify: `douban_assistant/classifier.py`
- Modify: `tests/test_tagging_rules.py`

- [ ] **Step 1: Write the failing test**

```python
def test_classify_book_maps_inferred_tags_to_project_categories() -> None:
    book = BookEntry(
        title="悉达多",
        url="https://example.com/book",
        authors=["黑塞"],
        pub_info="黑塞 / 天津人民出版社 / 2017",
        douban_tags=[],
        comment="小说里带着很多自我探索",
    )

    assert classify_book(book) == ["文学"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_classify_book_maps_inferred_tags_to_project_categories -v`
Expected: FAIL because category mapping still depends on old coarse rules

- [ ] **Step 3: Write minimal implementation**

```python
CATEGORY_FROM_TAGS: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        ("历史", ("历史",)),
        ("文学", ("小说", "散文", "诗", "文学")),
        ("社会学", ("社会",)),
        ("商业", ("商业",)),
        ("心理学", ("心理学",)),
        ("写作表达", ("写作",)),
        ("技术", ("技术",)),
    ]
)


def classify_book(book: BookEntry) -> list[str]:
    inferred_tags = infer_tags(book)
    matched: list[str] = []
    for category, tags in CATEGORY_FROM_TAGS.items():
        if any(tag in inferred_tags for tag in tags):
            matched.append(category)
    if not matched:
        matched.append("未分类")
    return matched
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_classify_book_maps_inferred_tags_to_project_categories -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/classifier.py tests/test_tagging_rules.py
git commit -m "feat: map inferred tags to project categories"
```

### Task 4: Persist Predicted Tags In Fetch And Parse Flows

**Files:**
- Modify: `douban_assistant/douban.py`
- Modify: `douban_assistant/cli.py`
- Modify: `tests/test_parsing.py`

- [ ] **Step 1: Write the failing test**

```python
def test_parse_html_output_includes_predicted_tags() -> None:
    fixture = Path("tests/fixtures/douban_collect_page_1.html").read_text(encoding="utf-8")
    books = parse_collect_page(fixture)
    books[0].predicted_tags = infer_tags(books[0])

    assert "商业" in books[0].predicted_tags
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_parsing.py::test_parse_html_output_includes_predicted_tags -v`
Expected: FAIL because predicted tags are not populated by normal flow

- [ ] **Step 3: Write minimal implementation**

```python
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
            categories=classify_book(book),
        )
        for book in books
    ]


def parse_html_command(html_path: Path) -> None:
    html = html_path.read_text(encoding="utf-8")
    books = parse_collect_page(html)
    for book in books:
        book.predicted_tags = infer_tags(book)
        book.categories = classify_book(book)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_parsing.py::test_parse_html_output_includes_predicted_tags -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add douban_assistant/douban.py douban_assistant/cli.py tests/test_parsing.py
git commit -m "feat: include predicted tags in outputs"
```

### Task 5: Cover Misleading Existing Tags And End-To-End Output

**Files:**
- Modify: `tests/test_tagging_rules.py`
- Modify: `tests/test_client_behavior.py`
- Modify: `README.md`

- [ ] **Step 1: Write the failing test**

```python
def test_infer_tags_can_override_sparse_existing_douban_tags() -> None:
    book = BookEntry(
        title="俄罗斯史（第八版）",
        url="https://example.com/book",
        authors=["尼古拉·梁赞诺夫斯基"],
        pub_info="上海人民出版社 / 2013",
        douban_tags=["政治"],
        comment="和中国史有些像",
    )

    assert "历史" in infer_tags(book)
    assert "政治" not in infer_tags(book)
```
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/test_tagging_rules.py::test_infer_tags_can_override_sparse_existing_douban_tags -v`
Expected: FAIL until inference logic prefers its own rule set over noisy source tags

- [ ] **Step 3: Write minimal implementation**

```python
def build_haystack(book: BookEntry) -> str:
    return " ".join(
        [
            book.title,
            " ".join(book.authors),
            book.pub_info,
            " ".join(book.douban_tags),
            book.comment,
        ]
    ).lower()


def infer_tags(book: BookEntry) -> list[str]:
    haystack = build_haystack(book)
    matched: list[str] = []
    for tag, keywords in TAG_RULES.items():
        if any(keyword.lower() in haystack for keyword in keywords):
            matched.append(tag)
    return dedupe_preserving_order(matched)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/test_tagging_rules.py -v`
Expected: PASS across tag inference and category mapping tests

- [ ] **Step 5: Commit**

```bash
git add tests/test_tagging_rules.py tests/test_client_behavior.py README.md douban_assistant/classifier.py
git commit -m "test: cover corrected tag inference behavior"
```

### Task 6: Verify Against Live And Fixture Data

**Files:**
- Test: `tests/test_cookie_loading.py`
- Test: `tests/test_client_behavior.py`
- Test: `tests/test_parsing.py`
- Test: `tests/test_tagging_rules.py`
- Manual verification: `data/books.json`

- [ ] **Step 1: Run the full targeted test suite**

Run: `python3 -m unittest tests.test_cookie_loading tests.test_client_behavior -v`
Expected: PASS

- [ ] **Step 2: Run parser and tagging tests**

Run: `python3 -m pytest tests/test_parsing.py tests/test_tagging_rules.py -v`
Expected: PASS

- [ ] **Step 3: Verify fixture CLI output**

Run: `python3 -m douban_assistant.cli parse-html tests/fixtures/douban_collect_page_1.html`
Expected: JSON output includes both `predicted_tags` and `categories`

- [ ] **Step 4: Verify live sync output**

Run: `python3 -m douban_assistant.cli sync --user-id 100654183 --max-pages 3 --cookie-file cookie.md --output data/books.json`
Expected: exit 0 and output file contains `douban_tags`, `predicted_tags`, and `categories`

- [ ] **Step 5: Commit**

```bash
git add data/books.json
git commit -m "chore: verify inferred tagging flow"
```
