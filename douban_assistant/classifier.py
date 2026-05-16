from __future__ import annotations

from collections import OrderedDict

from .models import BookEntry


TAG_RULES: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        ("历史", ("历史", "中国史", "世界史", "战争", "帝国", "王朝", "晚清", "俄国史", "俄罗斯史")),
        ("小说", ("小说", "虚构", "短篇")),
        ("散文", ("散文", "随笔")),
        ("诗", ("诗", "诗歌")),
        ("文学", ("文学",)),
        ("社会", ("社会", "阶层", "性别", "女性", "媒介", "传播", "人类学")),
        ("商业", ("商业", "品牌", "营销", "管理", "创业", "公司", "投资")),
        ("心理学", ("心理", "情绪", "关系", "成长", "认知", "人格", "自我探索")),
        ("写作表达", ("写作", "表达", "沟通", "采访", "叙事", "文案")),
        ("技术", ("计算机", "互联网", "编程", "算法", "人工智能", "AI", "产品")),
    ]
)

CATEGORY_FROM_TAGS: "OrderedDict[str, tuple[str, ...]]" = OrderedDict(
    [
        ("历史", ("历史",)),
        ("文学", ("小说", "散文", "诗", "文学")),
        ("社会学", ("社会",)),
        ("商业", ("商业",)),
        ("心理学", ("心理学",)),
        ("写作表达", ("写作表达",)),
        ("技术", ("技术",)),
    ]
)


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


def dedupe_preserving_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    deduped: list[str] = []
    for value in values:
        if value not in seen:
            deduped.append(value)
            seen.add(value)
    return deduped


def infer_tags(book: BookEntry) -> list[str]:
    haystack = build_haystack(book)
    matched: list[str] = []
    for tag, keywords in TAG_RULES.items():
        for keyword in keywords:
            if keyword.lower() in haystack:
                matched.append(tag)
                break
    return dedupe_preserving_order(matched)


def classify_book(book: BookEntry) -> list[str]:
    inferred_tags = book.predicted_tags or infer_tags(book)
    matched: list[str] = []
    for category, tags in CATEGORY_FROM_TAGS.items():
        for tag in tags:
            if tag in inferred_tags:
                matched.append(category)
                break

    if not matched:
        matched.append("未分类")
    return dedupe_preserving_order(matched)
