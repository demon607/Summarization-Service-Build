import datetime
from typing import TypedDict


class Article(TypedDict):
    id: int
    url: str
    title: str
    status: str
    content: str | None
    summary: str | None
    created_at: str
    error_message: str | None