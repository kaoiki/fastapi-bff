from datetime import datetime, timezone

from app.services.supabase import get_supabase_client


class FeedbackService:

    @staticmethod
    def submit_feedback(game_id: str, app_code: str, feedback_type: str, user_id: str = None):
        supabase = get_supabase_client()

        payload = {
            "game_id": game_id,
            "app_code": app_code,
            "type": feedback_type,
            "user_id": user_id,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        supabase.table("game_feedback").insert(payload).execute()

    @staticmethod
    def get_stats(app_code: str) -> dict:
        supabase = get_supabase_client()

        result = (
            supabase.table("game_feedback")
            .select("game_id, type")
            .eq("app_code", app_code)
            .execute()
        )

        rows = result.data or []

        stats = {}
        for row in rows:
            gid = row["game_id"]
            t = row["type"]
            if gid not in stats:
                stats[gid] = {"like": 0, "dislike": 0}
            if t in stats[gid]:
                stats[gid][t] += 1

        return stats
