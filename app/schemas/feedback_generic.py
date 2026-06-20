from pydantic import BaseModel, Field


class FeedbackRequest(BaseModel):
    category: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
