from pydantic import BaseModel, Field


class GameFeedbackRequest(BaseModel):
    game_id: str = Field(..., min_length=1)
    type: str = Field(..., pattern="^(like|dislike)$")
