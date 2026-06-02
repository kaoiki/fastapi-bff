from pydantic import BaseModel


class LeaderboardItem(BaseModel):
    game_name: str
    nickname: str
    avatar: str
    score: int
    play_date: str


class LeaderboardResponse(BaseModel):
    items: list[LeaderboardItem]


class TopPilotItem(BaseModel):
    nickname: str
    avatar: str
    first_place_count: int


class LeaderboardInitResponse(BaseModel):
    all_leaderboard: list[LeaderboardItem]
    top_3_pilots: list[TopPilotItem]