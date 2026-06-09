from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.api.health import router as health_router
from app.api.posts import router as posts_router
from app.api.comments import router as comments_router
from app.api.auth import router as auth_router
from app.api.game_score import router as game_score_router
from app.api.game_list import router as game_list_router
from app.api.leaderboard import router as leaderboard_router
from app.api.shop import router as shop_router
from app.api.services import router as services_router
from app.api.knowledge import router as knowledge_router, admin_router as knowledge_admin_router
from app.api.settings import router as settings_router
from app.core.config import settings
from app.core.exception_handler import register_exception_handlers

# uv run uvicorn app.main:app --reload

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug
)


@app.middleware("http")
async def cors_middleware(request: Request, call_next):
    # 直接处理 OPTIONS 预检请求
    if request.method == "OPTIONS":
        return Response(
            status_code=200,
            headers={
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "*",
                "Access-Control-Allow-Headers": "*",
                "Access-Control-Max-Age": "86400",
            }
        )

    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    return response


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
app.include_router(knowledge_router)
app.include_router(knowledge_admin_router)
app.include_router(settings_router)