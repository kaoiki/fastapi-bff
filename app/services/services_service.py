import json
from datetime import datetime, timezone
from uuid import uuid4

from app.core.exceptions import AppException
from app.schemas.services import CATEGORIES, FEE_TYPES
from app.services.supabase import get_supabase_client
from app.utils.storage_util import StorageUtil


SERVICE_IMAGE_BUCKET = "service-images"
MAX_SERVICE_IMAGES = 6


class ServicesService:

    # ── 校验 ──

    @staticmethod
    def _validate_service_data(data: dict, is_update: bool = False):
        category = data.get("category")
        if category and category not in CATEGORIES:
            raise AppException(code=400, message=f"Invalid category. Must be one of: {', '.join(CATEGORIES)}")

        fee_type = data.get("fee_type")
        if fee_type and fee_type not in FEE_TYPES:
            raise AppException(code=400, message=f"Invalid fee_type. Must be one of: {', '.join(FEE_TYPES)}")

        # 联系方式校验：创建时必须填，更新时仅在修改联系方式字段时才检查
        has_phone_key = "contact_phone" in data
        has_wechat_key = "contact_wechat" in data

        if not is_update:
            # 创建：至少填一个
            if not data.get("contact_phone") and not data.get("contact_wechat"):
                raise AppException(code=400, message="At least one contact method is required (phone or wechat)")
        else:
            # 更新：仅当传了联系方式字段时才校验
            if has_phone_key or has_wechat_key:
                phone = data.get("contact_phone")
                wechat = data.get("contact_wechat")
                if not phone and not wechat:
                    raise AppException(code=400, message="At least one contact method is required (phone or wechat)")

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

    # ── 图片工具方法 ──

    @staticmethod
    def _parse_images(raw):
        if not raw:
            return []
        if isinstance(raw, list):
            return raw
        if isinstance(raw, str):
            raw = raw.strip()
            if not raw:
                return []
            try:
                data = json.loads(raw)
                if isinstance(data, list):
                    return data
            except Exception:
                pass
        return []

    @staticmethod
    def _dump_images(images: list) -> str:
        return json.dumps(images, ensure_ascii=False)

    # ── CRUD ──

    @staticmethod
    def create_service(data: dict) -> dict:
        ServicesService._validate_service_data(data)

        supabase = get_supabase_client()
        result = supabase.table("services").insert(data).execute()

        rows = result.data or []
        if not rows:
            raise AppException(code=500, message="create service failed")

        return rows[0]

    @staticmethod
    def list_services(
        app_code: str,
        page: int = 1,
        page_size: int = 12,
        category: str = None,
    ):
        supabase = get_supabase_client()
        offset = (page - 1) * page_size

        query = (
            supabase.table("services")
            .select("*", count="exact")
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .eq("status", 0)
        )

        if category:
            query = query.eq("category", category)

        result = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        rows = result.data or []
        total = result.count or 0

        if not rows:
            return [], total

        # 批量查询用户昵称
        user_ids = list({r["user_id"] for r in rows if r.get("user_id")})
        user_map = {}
        if user_ids:
            user_resp = (
                supabase.table("auth_users")
                .select("id, nickname, avatar")
                .eq("app_code", app_code)
                .in_("id", user_ids)
                .execute()
            )
            for u in (user_resp.data or []):
                user_map[u["id"]] = u

        result_list = []
        for item in rows:
            user_info = user_map.get(item["user_id"], {})
            desc = item.get("description", "")
            truncated_desc = desc[:120] + "…" if len(desc) > 120 else desc

            result_list.append({
                "id": item["id"],
                "user_id": item["user_id"],
                "nickname": user_info.get("nickname", ""),
                "category": item["category"],
                "title": item["title"],
                "description": truncated_desc,
                "service_area": item.get("service_area"),
                "fee_type": item["fee_type"],
                "is_verified": item.get("is_verified", False),
                "provider_image": item.get("provider_image"),
                "created_at": item["created_at"],
            })

        return result_list, total

    @staticmethod
    def get_detail(service_id: str, app_code: str, current_user: dict = None):
        supabase = get_supabase_client()

        result = (
            supabase.table("services")
            .select("*")
            .eq("id", service_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            return None

        service = rows[0]

        # 查询发布者信息
        user_resp = (
            supabase.table("auth_users")
            .select("id, nickname, avatar")
            .eq("app_code", app_code)
            .eq("id", service["user_id"])
            .limit(1)
            .execute()
        )

        publisher = (user_resp.data or [{}])[0]

        # 联系方式仅登录用户可见
        show_contact = current_user is not None

        service_images = ServicesService._parse_images(service.get("service_images"))

        return {
            "id": service["id"],
            "user_id": service["user_id"],
            "nickname": publisher.get("nickname", ""),
            "avatar": publisher.get("avatar", ""),
            "category": service["category"],
            "title": service["title"],
            "description": service["description"],
            "contact_phone": service.get("contact_phone") if show_contact else None,
            "contact_wechat": service.get("contact_wechat") if show_contact else None,
            "service_area": service.get("service_area"),
            "available_time": service.get("available_time"),
            "fee_type": service["fee_type"],
            "is_verified": service.get("is_verified", False),
            "provider_image": service.get("provider_image"),
            "service_images": service_images,
            "service_image_count": len(service_images),
            "is_owner": current_user is not None and current_user["id"] == service["user_id"],
            "created_at": service["created_at"],
            "updated_at": service["updated_at"],
        }

    @staticmethod
    def update_service(service_id: str, app_code: str, user_id: str, data: dict) -> dict:
        supabase = get_supabase_client()

        # 查服务是否存在 + 所有权检查
        result = (
            supabase.table("services")
            .select("id, user_id")
            .eq("id", service_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=404, message="Service not found")

        service = rows[0]
        if service["user_id"] != user_id:
            raise AppException(code=403, message="Forbidden")

        # 校验传入字段
        ServicesService._validate_service_data(data, is_update=True)

        # 更新
        update_data = {k: v for k, v in data.items() if v is not None}
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()

        update_result = (
            supabase.table("services")
            .update(update_data)
            .eq("id", service_id)
            .execute()
        )

        updated_rows = update_result.data or []
        if not updated_rows:
            raise AppException(code=500, message="update service failed")

        return updated_rows[0]

    @staticmethod
    def delete_service(service_id: str, app_code: str, user_id: str) -> dict:
        supabase = get_supabase_client()

        result = (
            supabase.table("services")
            .select("id, user_id")
            .eq("id", service_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            raise AppException(code=404, message="Service not found")

        service = rows[0]
        if service["user_id"] != user_id:
            raise AppException(code=403, message="Forbidden")

        supabase.table("services").update({
            "is_deleted": True,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", service_id).execute()

        return {"id": service_id}

    # ── 图片上传 / 删除 ──

    @staticmethod
    def upload_provider_image(service_id: str, app_code: str, user_id: str, file_bytes: bytes, filename: str, content_type: str):
        """上传服务者头像"""
        supabase = get_supabase_client()

        result = (
            supabase.table("services")
            .select("id, user_id, provider_image")
            .eq("id", service_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            return {"error": "service_not_found"}

        service = rows[0]
        if service["user_id"] != user_id:
            return {"error": "forbidden"}

        # 删掉旧图
        old_image = service.get("provider_image")
        if old_image:
            old_path = None
            if isinstance(old_image, str) and old_image.startswith("http"):
                pass  # 外部 URL，不删除
            elif isinstance(old_image, dict) and old_image.get("path"):
                old_path = old_image["path"]
            if old_path:
                StorageUtil.delete_file(SERVICE_IMAGE_BUCKET, old_path)

        # 上传新图
        image_id = str(uuid4())
        suffix = "bin"
        if filename and "." in filename:
            suffix = filename.rsplit(".", 1)[-1].lower()

        path = f"services/{service_id}/provider_{image_id}.{suffix}"

        uploaded = StorageUtil.upload_bytes(
            bucket=SERVICE_IMAGE_BUCKET,
            path=path,
            file_bytes=file_bytes,
            content_type=content_type,
        )

        provider_image = {
            "id": image_id,
            "path": uploaded["path"],
            "url": uploaded["url"],
        }

        supabase.table("services").update({
            "provider_image": uploaded["url"],
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", service_id).eq("app_code", app_code).execute()

        return provider_image

    @staticmethod
    def upload_service_images(service_id: str, app_code: str, user_id: str, files: list):
        """上传资质佐证图（最多6张）"""
        supabase = get_supabase_client()

        result = (
            supabase.table("services")
            .select("id, user_id, service_images")
            .eq("id", service_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            return {"error": "service_not_found"}

        service = rows[0]
        if service["user_id"] != user_id:
            return {"error": "forbidden"}

        images = ServicesService._parse_images(service.get("service_images"))

        if len(images) >= MAX_SERVICE_IMAGES:
            return {"error": "image_limit_reached"}

        remain = MAX_SERVICE_IMAGES - len(images)
        upload_files = files[:remain]

        if not upload_files:
            return {"error": "image_limit_reached"}

        new_images = []
        for file in upload_files:
            content = file.file.read()
            image_id = str(uuid4())
            suffix = "bin"
            if file.filename and "." in file.filename:
                suffix = file.filename.rsplit(".", 1)[-1].lower()

            path = f"services/{service_id}/{image_id}.{suffix}"

            uploaded = StorageUtil.upload_bytes(
                bucket=SERVICE_IMAGE_BUCKET,
                path=path,
                file_bytes=content,
                content_type=file.content_type or "application/octet-stream",
            )

            new_images.append({
                "id": image_id,
                "path": uploaded["path"],
                "url": uploaded["url"],
            })

        images.extend(new_images)

        supabase.table("services").update({
            "service_images": ServicesService._dump_images(images),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", service_id).eq("app_code", app_code).execute()

        return {
            "images": images,
            "image_count": len(images),
        }

    @staticmethod
    def delete_service_image(service_id: str, image_id: str, app_code: str, user_id: str):
        """删除某张资质佐证图"""
        supabase = get_supabase_client()

        result = (
            supabase.table("services")
            .select("id, user_id, service_images")
            .eq("id", service_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        rows = result.data or []
        if not rows:
            return {"error": "service_not_found"}

        service = rows[0]
        if service["user_id"] != user_id:
            return {"error": "forbidden"}

        images = ServicesService._parse_images(service.get("service_images"))
        target = next((item for item in images if item.get("id") == image_id), None)

        if not target:
            return {"error": "image_not_found"}

        path = target.get("path")
        if path:
            StorageUtil.delete_file(SERVICE_IMAGE_BUCKET, path)

        next_images = [item for item in images if item.get("id") != image_id]

        supabase.table("services").update({
            "service_images": ServicesService._dump_images(next_images),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", service_id).eq("app_code", app_code).execute()

        return {
            "images": next_images,
            "image_count": len(next_images),
        }

    @staticmethod
    def list_my_services(app_code: str, user_id: str, page: int = 1, page_size: int = 12):
        supabase = get_supabase_client()
        offset = (page - 1) * page_size

        result = (
            supabase.table("services")
            .select("*", count="exact")
            .eq("app_code", app_code)
            .eq("user_id", user_id)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        rows = result.data or []
        total = result.count or 0

        # 查询当前用户信息
        user_resp = (
            supabase.table("auth_users")
            .select("nickname")
            .eq("app_code", app_code)
            .eq("id", user_id)
            .limit(1)
            .execute()
        )
        nickname = (user_resp.data or [{}])[0].get("nickname", "")

        result_list = []
        for item in rows:
            desc = item.get("description", "")
            truncated_desc = desc[:120] + "…" if len(desc) > 120 else desc

            result_list.append({
                "id": item["id"],
                "user_id": item["user_id"],
                "nickname": nickname,
                "category": item["category"],
                "title": item["title"],
                "description": truncated_desc,
                "service_area": item.get("service_area"),
                "fee_type": item["fee_type"],
                "is_verified": item.get("is_verified", False),
                "status": item.get("status", 0),
                "provider_image": item.get("provider_image"),
                "created_at": item["created_at"],
            })

        return result_list, total
