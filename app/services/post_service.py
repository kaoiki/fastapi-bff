import json
from uuid import uuid4

from app.services.supabase import get_supabase_client
from app.utils.storage_util import StorageUtil


POST_IMAGE_BUCKET = "post-images"
MAX_POST_IMAGES = 4


class PostService:
    @staticmethod
    def _parse_post_images(raw_cover_image):
        if not raw_cover_image:
            return []

        if isinstance(raw_cover_image, list):
            return raw_cover_image

        if isinstance(raw_cover_image, str):
            raw_cover_image = raw_cover_image.strip()
            if not raw_cover_image:
                return []

            try:
                data = json.loads(raw_cover_image)
                if isinstance(data, list):
                    return data
                if isinstance(data, str):
                    return [{"id": "cover", "url": data, "path": ""}]
            except Exception:
                return [{"id": "cover", "url": raw_cover_image, "path": ""}]

        return []

    @staticmethod
    def _dump_post_images(images: list):
        return json.dumps(images, ensure_ascii=False)

    @staticmethod
    async def create_post(data: dict):
        client = get_supabase_client()
        result = client.table("posts").insert(data).execute()
        return result.data or []

    @staticmethod
    async def list_posts(app_code: str, page: int, page_size: int):
        client = get_supabase_client()

        offset = (page - 1) * page_size

        post_result = (
            client.table("posts")
            .select("*", count="exact")
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .order("created_at", desc=True)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        posts = post_result.data or []
        total = post_result.count or 0

        if not posts:
            return [], total

        post_ids = [item["id"] for item in posts if item.get("id")]

        comment_count_map = {}

        if post_ids:
            comment_result = (
                client.table("comments")
                .select("post_id")
                .eq("app_code", app_code)
                .eq("is_deleted", False)
                .in_("post_id", post_ids)
                .execute()
            )

            comments = comment_result.data or []

            for item in comments:
                post_id = item.get("post_id")
                if not post_id:
                    continue
                comment_count_map[post_id] = comment_count_map.get(post_id, 0) + 1

        result_list = []
        for item in posts:
            post_id = item.get("id")
            images = PostService._parse_post_images(item.get("cover_image"))

            result_list.append({
                "id": item.get("id"),
                "title": item.get("title", ""),
                "content": item.get("content", ""),
                "created_at": item.get("created_at"),
                "comment_count": comment_count_map.get(post_id, 0),
                "image_count": len(images),
                "is_owner": False
            })

        return result_list, total

    @staticmethod
    async def get_post_detail(post_id: str, app_code: str):
        client = get_supabase_client()

        result = (
            client.table("posts")
            .select("*")
            .eq("id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        data = result.data or []
        if not data:
            return []

        post = data[0]
        comment_count = post.get("comment_count") or 0
        images = PostService._parse_post_images(post.get("cover_image"))
        image_count = len(images)

        return [{
            "id": post.get("id"),
            "title": post.get("title", ""),
            "content": post.get("content", ""),
            "created_at": post.get("created_at"),
            "user_id": post.get("user_id"),
            "comment_count": comment_count,
            "image_count": image_count,
            "images": images
        }]

    @staticmethod
    async def upload_post_images(
        post_id: str,
        app_code: str,
        user_id: str,
        files: list
    ):
        client = get_supabase_client()

        post_result = (
            client.table("posts")
            .select("id, user_id, cover_image")
            .eq("id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        post_list = post_result.data or []
        if not post_list:
            return {"error": "post_not_found"}

        post = post_list[0]
        if post.get("user_id") != user_id:
            return {"error": "forbidden"}

        images = PostService._parse_post_images(post.get("cover_image"))

        if len(images) >= MAX_POST_IMAGES:
            return {"error": "image_limit_reached"}

        remain = MAX_POST_IMAGES - len(images)
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

            path = f"posts/{post_id}/{image_id}.{suffix}"

            uploaded = StorageUtil.upload_bytes(
                bucket=POST_IMAGE_BUCKET,
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

        client.table("posts").update({
            "cover_image": PostService._dump_post_images(images)
        }).eq("id", post_id).eq("app_code", app_code).execute()

        return {
            "images": images,
            "image_count": len(images)
        }

    @staticmethod
    async def delete_post_image(
        post_id: str,
        image_id: str,
        app_code: str,
        user_id: str
    ):
        client = get_supabase_client()

        post_result = (
            client.table("posts")
            .select("id, user_id, cover_image")
            .eq("id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        post_list = post_result.data or []
        if not post_list:
            return {"error": "post_not_found"}

        post = post_list[0]
        if post.get("user_id") != user_id:
            return {"error": "forbidden"}

        images = PostService._parse_post_images(post.get("cover_image"))
        target = next((item for item in images if item.get("id") == image_id), None)

        if not target:
            return {"error": "image_not_found"}

        path = target.get("path")
        if path:
            StorageUtil.delete_file(POST_IMAGE_BUCKET, path)

        next_images = [item for item in images if item.get("id") != image_id]

        client.table("posts").update({
            "cover_image": PostService._dump_post_images(next_images)
        }).eq("id", post_id).eq("app_code", app_code).execute()

        return {
            "images": next_images,
            "image_count": len(next_images)
        }

    @staticmethod
    async def delete_post(post_id: str, app_code: str):
        client = get_supabase_client()

        post_result = (
            client.table("posts")
            .select("id, cover_image")
            .eq("id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        post_list = post_result.data or []
        if not post_list:
            return None
        post = post_list[0]
        images = PostService._parse_post_images(post.get("cover_image"))

        for item in images:
            path = item.get("path")
            if path:
                StorageUtil.delete_file(POST_IMAGE_BUCKET, path)

        client.table("posts").update({
            "is_deleted": True
        }).eq("id", post_id).eq("app_code", app_code).execute()

        client.table("comments").update({
            "is_deleted": True
        }).eq("post_id", post_id).eq("app_code", app_code).execute()

        return {"id": post_id}