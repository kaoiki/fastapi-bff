import json
from uuid import uuid4

from app.core.exceptions import AppException
from app.services.supabase import get_supabase_client
from app.utils.storage_util import StorageUtil


REVIEW_IMAGE_BUCKET = "review-images"
MAX_REVIEW_IMAGES = 4


class ShopService:

    # ── 图片工具方法（与 PostService 一致） ──

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
                if isinstance(data, str):
                    return [{"id": "cover", "url": data, "path": ""}]
            except Exception:
                return [{"id": "cover", "url": raw, "path": ""}]

        return []

    @staticmethod
    def _dump_images(images: list) -> str:
        return json.dumps(images, ensure_ascii=False)

    # ── 评测帖 CRUD ──

    @staticmethod
    async def create_review(data: dict):
        client = get_supabase_client()
        result = client.table("reviews").insert(data).execute()
        return result.data or []

    @staticmethod
    async def list_reviews(app_code: str, page: int, page_size: int):
        client = get_supabase_client()
        offset = (page - 1) * page_size

        result = (
            client.table("reviews")
            .select("*", count="exact")
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        reviews = result.data or []
        total = result.count or 0

        result_list = []
        for item in reviews:
            images = ShopService._parse_images(item.get("cover_image"))
            result_list.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "status": item.get("status", 0),
                "join_count": item.get("join_count", 0),
                "image_count": len(images),
                "created_at": item.get("created_at"),
                "user_id": item.get("user_id"),
            })

        return result_list, total

    @staticmethod
    async def get_review_detail(review_id: str, app_code: str):
        client = get_supabase_client()

        result = (
            client.table("reviews")
            .select("*")
            .eq("id", review_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        data = result.data or []
        if not data:
            return None

        review = data[0]
        images = ShopService._parse_images(review.get("cover_image"))

        return {
            "id": review.get("id"),
            "title": review.get("title", ""),
            "content": review.get("content", ""),
            "status": review.get("status", 0),
            "join_count": review.get("join_count", 0),
            "images": images,
            "image_count": len(images),
            "created_at": review.get("created_at"),
            "user_id": review.get("user_id"),
        }

    @staticmethod
    async def delete_review(review_id: str, app_code: str):
        client = get_supabase_client()

        result = (
            client.table("reviews")
            .select("id, cover_image")
            .eq("id", review_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        review_list = result.data or []
        if not review_list:
            return None

        review = review_list[0]
        images = ShopService._parse_images(review.get("cover_image"))

        for item in images:
            path = item.get("path")
            if path:
                StorageUtil.delete_file(REVIEW_IMAGE_BUCKET, path)

        client.table("reviews").update({
            "is_deleted": True
        }).eq("id", review_id).eq("app_code", app_code).execute()

        return {"id": review_id}

    # ── 图片上传 / 删除 ──

    @staticmethod
    async def upload_images(
        review_id: str,
        app_code: str,
        user_id: str,
        files: list,
    ):
        client = get_supabase_client()

        review_result = (
            client.table("reviews")
            .select("id, user_id, cover_image")
            .eq("id", review_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        review_list = review_result.data or []
        if not review_list:
            return {"error": "review_not_found"}

        review = review_list[0]
        if review.get("user_id") != user_id:
            return {"error": "forbidden"}

        images = ShopService._parse_images(review.get("cover_image"))

        if len(images) >= MAX_REVIEW_IMAGES:
            return {"error": "image_limit_reached"}

        remain = MAX_REVIEW_IMAGES - len(images)
        upload_files = files[:remain]

        if not upload_files:
            return {"error": "image_limit_reached"}

        new_images = []
        for file in upload_files:
            content = await file.read()
            image_id = str(uuid4())
            suffix = "bin"
            if file.filename and "." in file.filename:
                suffix = file.filename.rsplit(".", 1)[-1].lower()

            path = f"reviews/{review_id}/{image_id}.{suffix}"

            uploaded = StorageUtil.upload_bytes(
                bucket=REVIEW_IMAGE_BUCKET,
                path=path,
                file_bytes=content,
                content_type=file.content_type or "application/octet-stream"
            )

            new_images.append({
                "id": image_id,
                "path": uploaded["path"],
                "url": uploaded["url"]
            })

        images.extend(new_images)

        client.table("reviews").update({
            "cover_image": ShopService._dump_images(images)
        }).eq("id", review_id).eq("app_code", app_code).execute()

        return {
            "images": images,
            "image_count": len(images)
        }

    @staticmethod
    async def delete_image(
        review_id: str,
        image_id: str,
        app_code: str,
        user_id: str,
    ):
        client = get_supabase_client()

        review_result = (
            client.table("reviews")
            .select("id, user_id, cover_image")
            .eq("id", review_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        review_list = review_result.data or []
        if not review_list:
            return {"error": "review_not_found"}

        review = review_list[0]
        if review.get("user_id") != user_id:
            return {"error": "forbidden"}

        images = ShopService._parse_images(review.get("cover_image"))
        target = next((item for item in images if item.get("id") == image_id), None)

        if not target:
            return {"error": "image_not_found"}

        path = target.get("path")
        if path:
            StorageUtil.delete_file(REVIEW_IMAGE_BUCKET, path)

        next_images = [item for item in images if item.get("id") != image_id]

        client.table("reviews").update({
            "cover_image": ShopService._dump_images(next_images)
        }).eq("id", review_id).eq("app_code", app_code).execute()

        return {
            "images": next_images,
            "image_count": len(next_images)
        }

    # ── Join / Unjoin ──

    @staticmethod
    def toggle_join(review_id: str, app_code: str, user_id: str):
        client = get_supabase_client()

        # 先确认评测帖存在
        review_result = (
            client.table("reviews")
            .select("id, join_count")
            .eq("id", review_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        if not review_result.data:
            raise AppException(code=404, message="review not found")

        review = review_result.data[0]

        # 查是否已 join
        join_result = (
            client.table("review_joins")
            .select("id")
            .eq("review_id", review_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        already_joined = len(join_result.data or []) > 0

        if already_joined:
            # 取消 join + 递减计数
            client.table("review_joins") \
                .delete() \
                .eq("review_id", review_id) \
                .eq("user_id", user_id) \
                .execute()

            new_count = max(0, (review.get("join_count") or 0) - 1)
            client.table("reviews").update({
                "join_count": new_count
            }).eq("id", review_id).execute()
        else:
            # 加入 join + 递增计数
            client.table("review_joins").insert({
                "review_id": review_id,
                "user_id": user_id,
                "app_code": app_code,
            }).execute()

            new_count = (review.get("join_count") or 0) + 1
            client.table("reviews").update({
                "join_count": new_count
            }).eq("id", review_id).execute()

        return {
            "joined": not already_joined,
            "join_count": new_count,
        }

    @staticmethod
    def get_join_status(review_id: str, user_id: str) -> bool:
        """查询当前用户是否已 join 某个评测"""
        client = get_supabase_client()

        result = (
            client.table("review_joins")
            .select("id")
            .eq("review_id", review_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        return len(result.data or []) > 0
