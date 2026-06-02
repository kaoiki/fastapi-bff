from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.posts import router as posts_router
from app.api.comments import router as comments_router
from app.api.auth import router as auth_router
from app.api.game_score import router as game_score_router
from app.api.game_list import router as game_list_router
from app.api.leaderboard import router as leaderboard_router
from app.api.shop import router as shop_router
from app.api.services import router as services_router
from app.core.config import settings
from app.core.exception_handler import register_exception_handlers

# uv run uvicorn app.main:app --reload


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_allow_origins] if settings.cors_allow_origins != "*" else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(posts_router)
app.include_router(comments_router)
app.include_router(auth_router)
app.include_router(game_score_router)
app.include_router(game_list_router)
app.include_router(leaderboard_router)
app.include_router(shop_router)
app.include_router(services_router)
