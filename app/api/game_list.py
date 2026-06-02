from fastapi import APIRouter, Header

from app.core.response import success
from app.core.config import settings
from app.core.exceptions import AppException
from app.services.game_list_service import GameListService

router = APIRouter(
    prefix="/api/games",
    tags=["8bit-games"]
)


def _validate_app_code(x_app_code: str):
    if not x_app_code:
        raise AppException(code=400, message="x-app-code required")

    allowed = settings.get_allowed_app_codes()
    if x_app_code not in allowed:
        raise AppException(code=400, message="x-app-code not allowed")


@router.get("")
def get_game_list(x_app_code: str = Header(...)):
    _validate_app_code(x_app_code)

    rows = GameListService.get_active_games()

    return success(data={
        "items": rows
    })