from datetime import datetime, timezone

from app.core.exceptions import AppException
from app.services.supabase import get_supabase_client


class GameScoreService:

    @staticmethod
    def create_score(user_id: str, game_id: str, score: int):
        supabase = get_supabase_client()

        game_resp = (
            supabase.table("game_list")
            .select("id, game_id, game_name, status")
            .eq("game_id", game_id)
            .limit(1)
            .execute()
        )

        game_rows = game_resp.data or []
        if not game_rows:
            raise AppException(code=400, message="game_id not found")

        game = game_rows[0]
        if game["status"] != 1:
            raise AppException(code=400, message="game is unavailable")

        existing_resp = (
            supabase.table("game_scores")
            .select("id, user_id, game_id, score, play_date")
            .eq("user_id", user_id)
            .eq("game_id", game_id)
            .limit(1)
            .execute()
        )

        existing_rows = existing_resp.data or []

        if not existing_rows:
            payload = {
                "user_id": user_id,
                "game_id": game_id,
                "score": score,
                "play_date": datetime.now(timezone.utc).isoformat()
            }

            insert_resp = (
                supabase.table("game_scores")
                .insert(payload)
                .execute()
            )

            rows = insert_resp.data or []
            if not rows:
                raise Exception("create game score failed")

            return rows[0]

        existing = existing_rows[0]

        if score <= existing["score"]:
            return existing

        update_payload = {
            "score": score,
            "play_date": datetime.now(timezone.utc).isoformat()
        }

        update_resp = (
            supabase.table("game_scores")
            .update(update_payload)
            .eq("id", existing["id"])
            .execute()
        )

        rows = update_resp.data or []
        if not rows:
            raise Exception("update game score failed")

        return rows[0]