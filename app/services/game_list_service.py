from app.services.supabase import get_supabase_client


class GameListService:

    @staticmethod
    def get_active_games():
        supabase = get_supabase_client()

        resp = (
            supabase.table("game_list")
            .select("game_id, game_name, create_datetime")
            .eq("status", 1)
            .order("create_datetime", desc=True)
            .execute()
        )

        return resp.data or []