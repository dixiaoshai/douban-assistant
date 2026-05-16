from __future__ import annotations

from dataclasses import asdict, dataclass, field


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

    def to_dict(self) -> dict:
        return asdict(self)
