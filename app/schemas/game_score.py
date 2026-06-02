from pydantic import BaseModel, Field


class GameScoreCreateRequest(BaseModel):
    game_id: str = Field(..., min_length=1, max_length=100)
    score: int = Field(..., ge=0)


class GameScoreCreateResponse(BaseModel):
    id: str
    user_id: str
    game_id: str
    score: int
    play_date: str