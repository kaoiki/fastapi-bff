from fastapi import APIRouter, Depends

from app.core.response import success
from app.core.dependencies import require_app_user
from app.schemas.game_score import GameScoreCreateRequest
from app.services.game_score_service import GameScoreService

router = APIRouter(
    prefix="/api/game-scores",
    tags=["8bit-game-scores"]
)


@router.post("")
def create_game_score(
    req: GameScoreCreateRequest,
    current_user: dict = Depends(require_app_user("8bit"))
):
    row = GameScoreService.create_score(
        user_id=current_user["id"],
        game_id=req.game_id,
        score=req.score
    )

    return success(data=row)