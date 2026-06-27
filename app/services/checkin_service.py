import math
from datetime import date, timedelta

from app.core.exceptions import AppException
from app.services.supabase import get_supabase_client


class CheckinService:

    @staticmethod
    def list_checkins(user_id: str, app_code: str, page: int = 1, page_size: int = 10, mine: bool = False) -> tuple:
        supabase = get_supabase_client()
        offset = (page - 1) * page_size

        query = supabase.table("checkins").select("*", count="exact")

        if mine:
            query = query.eq("user_id", user_id)

        result = query.order("created_at", desc=True).range(offset, offset + page_size - 1).execute()

        rows = result.data or []
        total = result.count or 0

        if not rows:
            return [], total

        # 批量查用户、lesson、course 信息
        lesson_ids = list({r["lesson_id"] for r in rows})
        lesson_map = {}
        if lesson_ids:
            l_resp = (
                supabase.table("lessons")
                .select("id, name, course_id")
                .in_("id", lesson_ids)
                .execute()
            )
            course_ids = list({l["course_id"] for l in (l_resp.data or [])})
            course_map = {}
            if course_ids:
                c_resp = (
                    supabase.table("courses")
                    .select("id, name")
                    .in_("id", course_ids)
                    .execute()
                )
                for c in (c_resp.data or []):
                    course_map[c["id"]] = c["name"]
            for l in (l_resp.data or []):
                lesson_map[l["id"]] = {
                    "title": l["name"],
                    "course_name": course_map.get(l["course_id"], ""),
                }

        # 批量查用户信息
        all_user_ids = list({r["user_id"] for r in rows})
        user_map = {}
        if all_user_ids:
            user_resp = (
                supabase.table("auth_users")
                .select("id, nickname, avatar")
                .in_("id", all_user_ids)
                .execute()
            )
            for u in (user_resp.data or []):
                user_map[u["id"]] = {"nickname": u.get("nickname", ""), "avatar": u.get("avatar", "")}

        # 批量查 cheer 数据
        checkin_ids = [r["id"] for r in rows]
        cheer_count_map = {}
        cheered_set = set()

        if checkin_ids:
            cheer_resp = (
                supabase.table("checkin_cheers")
                .select("checkin_id, user_id")
                .in_("checkin_id", checkin_ids)
                .execute()
            )
            for cr in (cheer_resp.data or []):
                cid = cr["checkin_id"]
                cheer_count_map[cid] = cheer_count_map.get(cid, 0) + 1
                if cr["user_id"] == user_id:
                    cheered_set.add(cid)

        result_list = []
        for r in rows:
            cid = r["id"]
            info = lesson_map.get(r["lesson_id"], {})
            u = user_map.get(r["user_id"], {"nickname": "", "avatar": ""})
            result_list.append({
                "id": cid,
                "user": {
                    "nickname": u["nickname"],
                    "avatar": u["avatar"],
                },
                "lesson": info.get("title", ""),
                "course": info.get("course_name", ""),
                "type": r["type"],
                "accuracy": r["accuracy"],
                "time": r["time_seconds"],
                "xp": r["xp_earned"],
                "coins": r["coins_earned"],
                "cheer_count": cheer_count_map.get(cid, 0),
                "cheered": cid in cheered_set,
                "created_at": r["created_at"],
            })

        return result_list, total

    @staticmethod
    def toggle_cheer(checkin_id: str, user_id: str) -> dict:
        supabase = get_supabase_client()

        # 确认 checkin 存在
        checkin_resp = (
            supabase.table("checkins")
            .select("id, user_id")
            .eq("id", checkin_id)
            .limit(1)
            .execute()
        )

        if not checkin_resp.data:
            raise AppException(code=404, message="Checkin not found")

        # 不能给自己加油
        if checkin_resp.data[0]["user_id"] == user_id:
            raise AppException(code=400, message="Cannot cheer your own checkin")

        # 查是否已加油
        cheer_resp = (
            supabase.table("checkin_cheers")
            .select("id")
            .eq("checkin_id", checkin_id)
            .eq("user_id", user_id)
            .limit(1)
            .execute()
        )

        existing = cheer_resp.data[0] if cheer_resp.data else None

        if existing:
            supabase.table("checkin_cheers").delete().eq("id", existing["id"]).execute()
            cheered = False
        else:
            supabase.table("checkin_cheers").insert({
                "checkin_id": checkin_id,
                "user_id": user_id,
            }).execute()
            cheered = True

        # 重新计数
        count_resp = (
            supabase.table("checkin_cheers")
            .select("id", count="exact")
            .eq("checkin_id", checkin_id)
            .execute()
        )
        cheer_count = count_resp.count or 0

        return {"cheered": cheered, "cheer_count": cheer_count}

    @staticmethod
    def get_leaders(mode: str, app_code: str) -> list:
        supabase = get_supabase_client()

        from datetime import datetime

        query = supabase.table("checkins").select("user_id", count="exact")

        if mode == "today":
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
            query = query.gte("created_at", today_start)

        result = query.execute()
        rows = result.data or []

        # 按 user_id 计数
        count_map = {}
        for r in rows:
            uid = r["user_id"]
            count_map[uid] = count_map.get(uid, 0) + 1

        if not count_map:
            return []

        # 取 Top 3
        top = sorted(count_map.items(), key=lambda x: x[1], reverse=True)[:3]
        top_ids = [uid for uid, _ in top]

        # 查昵称
        user_resp = (
            supabase.table("auth_users")
            .select("id, nickname")
            .in_("id", top_ids)
            .execute()
        )
        nickname_map = {u["id"]: u["nickname"] for u in (user_resp.data or [])}

        return [
            {"nickname": nickname_map.get(uid, ""), "count": count}
            for uid, count in top
        ]

    @staticmethod
    def get_activity(user_id: str, app_code: str) -> dict:
        supabase = get_supabase_client()

        today = date.today()
        thirty_days_ago = today - timedelta(days=29)

        # 取最近 30 天的打卡记录
        result = (
            supabase.table("checkins")
            .select("created_at")
            .eq("user_id", user_id)
            .gte("created_at", thirty_days_ago.isoformat())
            .execute()
        )

        rows = result.data or []

        # 按日期计数
        count_map = {}
        for r in rows:
            d = r["created_at"][:10]
            count_map[d] = count_map.get(d, 0) + 1

        # 生成 30 天数组
        days = []
        for i in range(30):
            d = thirty_days_ago + timedelta(days=i)
            count = count_map.get(d.isoformat(), 0)
            activity = min(round(math.sqrt(count)), 10)
            days.append(activity)

        return {"days": days}
