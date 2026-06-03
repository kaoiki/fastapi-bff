from fastapi import APIRouter, Depends, Header, Query

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base, require_knowledge_admin
from app.core.response import fail, success
from app.schemas.knowledge import CreateArticleRequest, UpdateArticleRequest
from app.services.knowledge_service import KnowledgeService

# ── 公开路由 ──

router = APIRouter(prefix="/api/v1/knowledge", tags=["knowledge"])


@router.get("/articles")
def list_articles(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    category: str = Query(None),
    keyword: str = Query(None),
    is_featured: bool = Query(None),
    is_hot: bool = Query(None),
    app_code: str = Depends(get_app_code),
):
    data, total = KnowledgeService.list_articles(
        app_code=app_code,
        page=page,
        page_size=page_size,
        category=category,
        keyword=keyword,
        is_featured=is_featured,
        is_hot=is_hot,
    )

    total_page = (total + page_size - 1) // page_size

    return success(data={
        "list": data,
        "total": total,
        "total_page": total_page,
        "page": page,
        "page_size": page_size,
    })


@router.get("/articles/hot")
def get_hot_articles(
    limit: int = Query(10, ge=1, le=50),
    app_code: str = Depends(get_app_code),
):
    data = KnowledgeService.get_hot_articles(app_code, limit)
    return success(data={"list": data})


@router.get("/articles/featured")
def get_featured_articles(
    limit: int = Query(10, ge=1, le=50),
    app_code: str = Depends(get_app_code),
):
    data = KnowledgeService.get_featured_articles(app_code, limit)
    return success(data={"list": data})


@router.get("/articles/latest")
def get_latest_articles(
    limit: int = Query(10, ge=1, le=50),
    app_code: str = Depends(get_app_code),
):
    data = KnowledgeService.get_latest_articles(app_code, limit)
    return success(data={"list": data})


@router.get("/articles/slug/{slug}")
def get_article_by_slug(
    slug: str,
    app_code: str = Depends(get_app_code),
    authorization: str = Header(default=None),
):
    current_user = KnowledgeService._resolve_user_from_token(authorization, app_code)

    data = KnowledgeService.get_article_by_slug(slug, app_code, current_user)

    if not data:
        return fail(code=404, message="Article not found", data=None)

    return success(data={"article": data})


@router.get("/articles/{article_id}")
def get_article_by_id(
    article_id: str,
    app_code: str = Depends(get_app_code),
    authorization: str = Header(default=None),
):
    current_user = KnowledgeService._resolve_user_from_token(authorization, app_code)

    data = KnowledgeService.get_article_by_id(article_id, app_code, current_user)

    if not data:
        return fail(code=404, message="Article not found", data=None)

    return success(data={"article": data})


@router.get("/categories")
def get_categories():
    data = KnowledgeService.get_categories()
    return success(data=data)


# ── 管理路由 ──

admin_router = APIRouter(prefix="/api/v1/admin/knowledge", tags=["knowledge-admin"])


@admin_router.post("/articles")
def create_article(
    request: CreateArticleRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(require_knowledge_admin),
):
    data = request.model_dump()
    data["app_code"] = app_code

    result = KnowledgeService.create_article(data)
    return success(data=result)


@admin_router.put("/articles/{article_id}")
def update_article(
    article_id: str,
    request: UpdateArticleRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(require_knowledge_admin),
):
    data = {k: v for k, v in request.model_dump().items() if v is not None}

    if not data:
        return fail(code=400, message="No fields to update", data=None)

    result = KnowledgeService.update_article(article_id, app_code, data)
    return success(data=result)


@admin_router.delete("/articles/{article_id}")
def delete_article(
    article_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(require_knowledge_admin),
):
    result = KnowledgeService.delete_article(article_id, app_code)
    return success(data=result)
