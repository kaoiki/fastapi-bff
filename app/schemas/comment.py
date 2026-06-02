from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class CreateCommentRequest(BaseModel):
    post_id: UUID
    content: str = Field(..., min_length=1, max_length=2000)
    user_id: str = Field(..., min_length=1)


class CommentItem(BaseModel):
    id: str
    post_id: str
    content: str
    user_id: str
    like_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None