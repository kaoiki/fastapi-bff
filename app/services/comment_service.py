from app.services.supabase import get_supabase_client


class CommentService:
    @staticmethod
    async def create_comment(data: dict):
        client = get_supabase_client()

        post_result = (
            client.table("posts")
            .select("id, comment_count")
            .eq("id", data["post_id"])
            .eq("app_code", data["app_code"])
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        post_list = post_result.data or []
        if not post_list:
            return None

        insert_data = {
            "post_id": data["post_id"],
            "app_code": data["app_code"],
            "content": data["content"],
            "user_id": data["user_id"],
        }

        comment_result = client.table("comments").insert(insert_data).execute()
        comment_list = comment_result.data or []

        current_count = post_list[0].get("comment_count") or 0
        new_count = current_count + 1

        client.table("posts").update({
            "comment_count": new_count
        }).eq("id", data["post_id"]).eq("app_code", data["app_code"]).execute()

        return comment_list

    @staticmethod
    async def list_comments(post_id: str, app_code: str, page: int, page_size: int):
        client = get_supabase_client()

        post_result = (
            client.table("posts")
            .select("id")
            .eq("id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        post_list = post_result.data or []
        if not post_list:
            return None, 0

        offset = (page - 1) * page_size

        result = (
            client.table("comments")
            .select("*", count="exact")
            .eq("post_id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .order("created_at", desc=False)
            .range(offset, offset + page_size - 1)
            .execute()
        )

        return result.data or [], result.count or 0
        
    @staticmethod
    async def delete_comment(comment_id: str, app_code: str):
        client = get_supabase_client()

        comment_result = (
            client.table("comments")
            .select("id, post_id")
            .eq("id", comment_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        comment_list = comment_result.data or []
        if not comment_list:
            return None

        comment = comment_list[0]
        post_id = comment["post_id"]

        post_result = (
            client.table("posts")
            .select("id, comment_count")
            .eq("id", post_id)
            .eq("app_code", app_code)
            .eq("is_deleted", False)
            .limit(1)
            .execute()
        )

        post_list = post_result.data or []
        if not post_list:
            return None

        client.table("comments").update({
            "is_deleted": True
        }).eq("id", comment_id).eq("app_code", app_code).execute()

        current_count = post_list[0].get("comment_count") or 0
        new_count = current_count - 1 if current_count > 0 else 0

        client.table("posts").update({
            "comment_count": new_count
        }).eq("id", post_id).eq("app_code", app_code).execute()

        return {"id": comment_id}



