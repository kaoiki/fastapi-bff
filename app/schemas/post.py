from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreatePostRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1, max_length=100)
    cover_image: Optional[str] = None


class PostItem(BaseModel):
    id: str
    app_code: str
    title: str
    content: str
    user_id: str
    cover_image: Optional[str] = None
    like_count: int
    comment_count: int
    view_count: int
    is_deleted: bool
    created_at: datetime
    updated_at: datetime