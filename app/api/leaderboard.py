from fastapi import APIRouter, Header

from app.core.response import success
from app.core.config import settings
from app.core.exceptions import AppException
from app.services.leaderboard_service import LeaderboardService

router = APIRouter(
    prefix="/api/leaderboard",
    tags=["8bit-leaderboard"]
)


def _validate_app_code(x_app_code: str):
    if not x_app_code:
        raise AppException(code=400, message="x-app-code required")

    allowed = settings.get_allowed_app_codes()
    if x_app_code not in allowed:
        raise AppException(code=400, message="x-app-code not allowed")


@router.get("/init")
def get_leaderboard_init(x_app_code: str = Header(...)):
    _validate_app_code(x_app_code)

    data = LeaderboardService.get_leaderboard_init(app_code=x_app_code)

    return success(data=data)


@router.get("/{game_id}")
def get_leaderboard(game_id: str, x_app_code: str = Header(...)):
    _validate_app_code(x_app_code)

    rows = LeaderboardService.get_top_scores(
        game_id=game_id,
        app_code=x_app_code
    )

    return success(data={
        "items": rows
    })