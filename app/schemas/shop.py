from typing import Optional

from pydantic import BaseModel, Field


class CreateReviewRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)
