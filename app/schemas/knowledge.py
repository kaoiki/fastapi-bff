from typing import Optional

from pydantic import BaseModel, Field


CATEGORIES = [
    {"code": "prepare", "name": "准备养"},
    {"code": "new_owner", "name": "刚开始养"},
    {"code": "common", "name": "常见困惑"},
    {"code": "health", "name": "健康与风险"},
    {"code": "practice", "name": "我的实践记录"},
]

CATEGORY_CODES = [c["code"] for c in CATEGORIES]

SOURCE_TYPES = ["official", "practice", "review", "reference"]


class CreateArticleRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    slug: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1)
    summary: Optional[str] = None
    content_markdown: str = Field(..., min_length=1)
    cover_image: Optional[str] = None
    source_type: str = "official"
    status: int = 1
    sort_order: int = 0
    is_featured: bool = False
    is_hot: bool = False
    require_login: bool = False


class UpdateArticleRequest(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    slug: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[str] = None
    summary: Optional[str] = None
    content_markdown: Optional[str] = None
    cover_image: Optional[str] = None
    source_type: Optional[str] = None
    status: Optional[int] = None
    sort_order: Optional[int] = None
    is_featured: Optional[bool] = None
    is_hot: Optional[bool] = None
    require_login: Optional[bool] = None
