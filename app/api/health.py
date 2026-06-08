import subprocess

from fastapi import APIRouter

from app.core.config import settings
from app.core.response import success, fail
from app.services.supabase import get_supabase_client

router = APIRouter(prefix="/api", tags=["health"])


def _get_git_commit() -> str:
    try:
        repo_root = subprocess.check_output(
            ["git", "rev-parse", "--show-toplevel"],
            stderr=subprocess.DEVNULL,
        ).decode("utf-8").strip()
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            stderr=subprocess.DEVNULL,
            cwd=repo_root,
        ).decode("utf-8").strip()
    except Exception:
        return "unknown"


@router.get("/health")
async def health():
    return success(
        data={
            "app_name": settings.app_name,
            "version": settings.app_version,
            "commit": _get_git_commit(),
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