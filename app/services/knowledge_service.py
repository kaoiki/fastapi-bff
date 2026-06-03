from datetime import datetime, timezone

from app.core.exceptions import AppException
from app.schemas.knowledge import CATEGORIES, CATEGORY_CODES, SOURCE_TYPES
from app.services.supabase import get_supabase_client


class KnowledgeService:

    # ── 校验 ──

    @staticmethod
    def _validate_article(data: dict, is_update: bool = False):
        category = data.get("category")
        if category and category not in CATEGORY_CODES:
            raise AppException(code=400, message=f"Invalid category. Must be one of: {', '.join(CATEGORY_CODES)}")

        source_type = data.get("source_type")
        if source_type and source_type not in SOURCE_TYPES:
            raise AppException(code=400, message=f"Invalid source_type. Must be one of: {', '.join(SOURCE_TYPES)}")

        status = data.get("status")
        if status is not None and status not in (0, 1, 9):
            raise AppException(code=400, message="Invalid status. Must be 0 (draft), 1 (published), or 9 (deleted)")

    # ── Token → User 解析（供详情接口可选登录用） ──

    @staticmethod
    def _resolve_user_from_token(authorization: str, app_code: str):
        """尝试从 Authorization header 解析用户，失败返回 None"""
        if not authorization:
            return None

        token = authorization.strip()
        if token.lower().startswith("bearer "):
            token = token[7:].strip()

        if not token:
            return None

        supabase = get_supabase_client()

        token_resp = (
            supabase.table("auth_session_tokens")
            .select("user_id, expires_at, status")
            .eq("token", token)
            .limit(1)
            .execute()
        )

        rows = token_resp.data or []
        if not rows:
            return None

        session = rows[0]
        if session.get("status") != 1:
            return None

        expires_at = session.get("expires_at")
        if expires_at:
            expire_dt = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if expire_dt < datetime.now(timezone.utc):
                return None

        return {"id": session["user_id"]}

    # ── 公开接口 ──

    @staticmethod
    def list_articles(
        app_code: str,
        page: int = 1,
        page_size: int = 10,
        category: str = None,
        keyword: str = None,
        is_featured: bool = None,
        is_hot: bool = None,
    ):
        supabase = get_supabase_client()
        offset = (page - 1) * page_size

        query = (
            supabase.table("knowledge_articles")
            .select("*", count="exact")
            .eq("app_code", app_code)
            .eq("status", 1)
        )

        if category:
            query = query.eq("category", category)

        if is_featured is not None:
            query = query.eq("is_featured", is_featured)

        if is_hot is not None:
            query = query.eq("is_hot", is_hot)

        if keyword:
            query = query.or_(f"title.ilike.%{keyword}%,summary.ilike.%{keyword}%")

        result = query.order("sort_order", desc=False).order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        rows = result.data or []
        total = result.count or 0

        result_list = []
        for item in rows:
            result_list.append({
                "id": item["id"],
                "title": item["title"],
                "slug": item["slug"],
                "category": item["category"],
                "summary": item.get("summary", ""),
                "cover_image": item.get("cover_image"),
                "source_type": item["source_type"],
                "view_count": item.get("view_count", 0),
                "is_featured": item.get("is_featured", False),
                "is_hot": item.get("is_hot", False),
                "require_login": item.get("require_login", False),
                "created_at": item["created_at"],
                "updated_at": item["updated_at"],
            })

        return result_list, total

    @staticmethod
    def get_article_by_id(article_id: str, app_code: str, current_user: dict = None):
        supabase = get_supabase_client()

        result = (
            supabase.table("knowledge_articles")
            .select("*")
            .eq("id", article_id)
            .eq("app_code", app_code)
            .eq("status", 1)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            return None

        article = rows[0]

        show_content = not article.get("require_login", False) or current_user is not None

        return KnowledgeService._format_article(article, show_content=show_content)

    @staticmethod
    def get_article_by_slug(slug: str, app_code: str, current_user: dict = None):
        supabase = get_supabase_client()

        result = (
            supabase.table("knowledge_articles")
            .select("*")
            .eq("slug", slug)
            .eq("app_code", app_code)
            .eq("status", 1)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            return None

        article = rows[0]

        show_content = not article.get("require_login", False) or current_user is not None

        # 阅读数 +1
        supabase.table("knowledge_articles").update({
            "view_count": (article.get("view_count") or 0) + 1,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", article["id"]).execute()

        return KnowledgeService._format_article(article, show_content=show_content)

    @staticmethod
    def _format_article(item: dict, show_content: bool = True) -> dict:
        return {
            "id": item["id"],
            "title": item["title"],
            "slug": item["slug"],
            "category": item["category"],
            "summary": item.get("summary", ""),
            "content_markdown": item.get("content_markdown", "") if show_content else None,
            "cover_image": item.get("cover_image"),
            "source_type": item["source_type"],
            "view_count": item.get("view_count", 0),
            "is_featured": item.get("is_featured", False),
            "is_hot": item.get("is_hot", False),
            "require_login": item.get("require_login", False),
            "created_at": item["created_at"],
            "updated_at": item["updated_at"],
        }

    @staticmethod
    def get_hot_articles(app_code: str, limit: int = 10):
        supabase = get_supabase_client()

        result = (
            supabase.table("knowledge_articles")
            .select("id, title, slug, category, summary, cover_image, source_type, view_count, is_featured, is_hot, created_at, updated_at")
            .eq("app_code", app_code)
            .eq("status", 1)
            .eq("is_hot", True)
            .order("sort_order", desc=False)
            .limit(limit)
            .execute()
        )

        return result.data or []

    @staticmethod
    def get_featured_articles(app_code: str, limit: int = 10):
        supabase = get_supabase_client()

        result = (
            supabase.table("knowledge_articles")
            .select("id, title, slug, category, summary, cover_image, source_type, view_count, is_featured, is_hot, created_at, updated_at")
            .eq("app_code", app_code)
            .eq("status", 1)
            .eq("is_featured", True)
            .order("sort_order", desc=False)
            .limit(limit)
            .execute()
        )

        return result.data or []

    @staticmethod
    def get_latest_articles(app_code: str, limit: int = 10):
        supabase = get_supabase_client()

        result = (
            supabase.table("knowledge_articles")
            .select("id, title, slug, category, summary, cover_image, source_type, view_count, is_featured, is_hot, created_at, updated_at")
            .eq("app_code", app_code)
            .eq("status", 1)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )

        return result.data or []

    @staticmethod
    def get_categories():
        return CATEGORIES

    # ── 管理接口 ──

    @staticmethod
    def create_article(data: dict) -> dict:
        KnowledgeService._validate_article(data)

        supabase = get_supabase_client()

        # 检查 slug 唯一性
        existing = (
            supabase.table("knowledge_articles")
            .select("id")
            .eq("app_code", data["app_code"])
            .eq("slug", data["slug"])
            .limit(1)
            .execute()
        )

        if existing.data:
            raise AppException(code=400, message=f"Slug '{data['slug']}' already exists")

        result = supabase.table("knowledge_articles").insert(data).execute()

        rows = result.data or []
        if not rows:
            raise AppException(code=500, message="create article failed")

        return rows[0]

    @staticmethod
    def update_article(article_id: str, app_code: str, data: dict) -> dict:
        KnowledgeService._validate_article(data, is_update=True)

        supabase = get_supabase_client()

        # 检查文章存在
        existing = (
            supabase.table("knowledge_articles")
            .select("id")
            .eq("id", article_id)
            .eq("app_code", app_code)
            .limit(1)
            .execute()
        )

        if not existing.data:
            raise AppException(code=404, message="Article not found")

        # 检查 slug 唯一性（如果修改了 slug）
        slug = data.get("slug")
        if slug:
            slug_conflict = (
                supabase.table("knowledge_articles")
                .select("id")
                .eq("app_code", app_code)
                .eq("slug", slug)
                .neq("id", article_id)
                .limit(1)
                .execute()
            )
            if slug_conflict.data:
                raise AppException(code=400, message=f"Slug '{slug}' already exists")

        # 只更新非 None 字段
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        result = (
            supabase.table("knowledge_articles")
            .update(update_data)
            .eq("id", article_id)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=500, message="update article failed")

        return rows[0]

    @staticmethod
    def delete_article(article_id: str, app_code: str) -> dict:
        supabase = get_supabase_client()

        existing = (
            supabase.table("knowledge_articles")
            .select("id")
            .eq("id", article_id)
            .eq("app_code", app_code)
            .limit(1)
            .execute()
        )

        if not existing.data:
            raise AppException(code=404, message="Article not found")

        supabase.table("knowledge_articles").update({
            "status": 9,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", article_id).execute()

        return {"id": article_id}
