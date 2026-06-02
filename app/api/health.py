from fastapi import APIRouter

from app.core.config import settings
from app.core.response import success, fail
from app.services.supabase import get_supabase_client

router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
async def health():
    return success(
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "status": "ok"
        }
    )


@router.get("/health/supabase")
async def health_supabase():
    try:
        client = get_supabase_client()

        return success(
            data={
                "status": "ok",
                "supabase": "connected",
                "url": settings.supabase_url
            }
        )
    except Exception as e:
        return fail(
            code=500,
            message="supabase connection failed",
            data=str(e)
        )