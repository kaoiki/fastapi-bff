from pydantic import BaseModel


class GameItem(BaseModel):
    game_id: str
    game_name: str


class GameListResponse(BaseModel):
    items: list[GameItem]