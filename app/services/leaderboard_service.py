from app.services.supabase import get_supabase_client
from app.core.exceptions import AppException


class LeaderboardService:

    @staticmethod
    def get_top_scores(game_id: str, app_code: str, limit: int = 10):
        supabase = get_supabase_client()

        game_resp = (
            supabase.table("game_list")
            .select("game_name")
            .eq("game_id", game_id)
            .eq("status", 1)
            .limit(1)
            .execute()
        )

        if not game_resp.data:
            raise AppException(code=400, message="game not found or disabled")

        game_name = game_resp.data[0]["game_name"]

        score_resp = (
            supabase.table("game_scores")
            .select("user_id, score, play_date")
            .eq("game_id", game_id)
            .order("score", desc=True)
            .order("play_date", desc=False)
            .limit(limit)
            .execute()
        )

        score_rows = score_resp.data or []
        if not score_rows:
            return []

        user_ids = [row["user_id"] for row in score_rows if row.get("user_id")]

        user_resp = (
            supabase.table("auth_users")
            .select("id, nickname, avatar")
            .eq("app_code", app_code)
            .in_("id", user_ids)
            .execute()
        )

        user_map = {
            row["id"]: {
                "nickname": row.get("nickname", ""),
                "avatar": row.get("avatar", "")
            }
            for row in (user_resp.data or [])
        }

        result = []
        for row in score_rows:
            user_info = user_map.get(row["user_id"])
            if not user_info:
                continue

            result.append({
                "game_name": game_name,
                "nickname": user_info["nickname"],
                "avatar": user_info["avatar"],
                "score": row["score"],
                "play_date": row["play_date"]
            })

        return result

    @staticmethod
    def get_leaderboard_init(app_code: str):
        supabase = get_supabase_client()

        game_resp = (
            supabase.table("game_list")
            .select("game_id, game_name")
            .eq("status", 1)
            .order("create_datetime", desc=True)
            .execute()
        )

        game_rows = game_resp.data or []

        all_leaderboard = []
        first_place_counter = {}

        for game in game_rows:
            game_id = game["game_id"]
            game_name = game["game_name"]

            score_resp = (
                supabase.table("game_scores")
                .select("user_id, score, play_date")
                .eq("game_id", game_id)
                .order("score", desc=True)
                .order("play_date", desc=False)
                .limit(1)
                .execute()
            )

            score_rows = score_resp.data or []
            if not score_rows:
                continue

            top_score = score_rows[0]
            user_id = top_score.get("user_id")
            if not user_id:
                continue

            user_resp = (
                supabase.table("auth_users")
                .select("id, nickname, avatar")
                .eq("app_code", app_code)
                .eq("id", user_id)
                .limit(1)
                .execute()
            )

            user_rows = user_resp.data or []
            if not user_rows:
                continue

            user = user_rows[0]

            all_leaderboard.append({
                "game_name": game_name,
                "nickname": user.get("nickname", ""),
                "avatar": user.get("avatar", ""),
                "score": top_score["score"],
                "play_date": top_score["play_date"]
            })

            if user_id not in first_place_counter:
                first_place_counter[user_id] = {
                    "nickname": user.get("nickname", ""),
                    "avatar": user.get("avatar", ""),
                    "first_place_count": 0
                }

            first_place_counter[user_id]["first_place_count"] += 1

        top_3_pilots = sorted(
            first_place_counter.values(),
            key=lambda x: x["first_place_count"],
            reverse=True
        )[:3]

        return {
            "all_leaderboard": all_leaderboard,
            "top_3_pilots": top_3_pilots
        }