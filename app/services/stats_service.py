from datetime import date, datetime, timezone, timedelta

from app.services.supabase import get_supabase_client


class StatsService:

    @staticmethod
    def get_stats(user_id: str, app_code: str) -> dict:
        supabase = get_supabase_client()

        today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

        # 所有 records
        records_resp = (
            supabase.table("lesson_records")
            .select("xp_earned, coins_earned, total_questions, time_seconds, completed_at")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .execute()
        )

        all_records = records_resp.data or []

        # 总数据
        total_xp = sum(r.get("xp_earned", 0) or 0 for r in all_records)
        total_coins = sum(r.get("coins_earned", 0) or 0 for r in all_records)
        total_lessons = len(all_records)
        total_words = sum(r.get("total_questions", 0) or 0 for r in all_records)
        total_time = sum(r.get("time_seconds", 0) or 0 for r in all_records)

        # 今日数据
        today_records = [r for r in all_records if r.get("completed_at", "") >= today_start]
        today_time = sum(r.get("time_seconds", 0) or 0 for r in today_records)
        today_words = sum(r.get("total_questions", 0) or 0 for r in today_records)
        today_xp = sum(r.get("xp_earned", 0) or 0 for r in today_records)

        # 今日平均准确率
        today_correct = 0
        today_total_q = 0
        # 修正：需要从 lesson_records 取 correct_count 和 total_questions
        # 当前 select 没取 correct_count，需要补查
        today_detail = (
            supabase.table("lesson_records")
            .select("correct_count, total_questions")
            .eq("user_id", user_id)
            .gte("completed_at", today_start)
            .execute()
        )
        for r in (today_detail.data or []):
            today_correct += r.get("correct_count", 0) or 0
            today_total_q += r.get("total_questions", 0) or 0
        today_accuracy = round(today_correct / today_total_q * 100) if today_total_q > 0 else 0

        # 连续学习天数
        streak_days = StatsService._calc_streak_days(all_records)

        # 今日任务
        today_missions = [
            {"id": 1, "label": "Complete one battle", "done": len(today_records) >= 1, "progress": ""},
            {"id": 2, "label": "Practice 10 minutes", "done": today_time >= 600, "progress": f"{min(today_time, 600) // 60}/{10} min"},
            {"id": 3, "label": "Learn 20 words", "done": today_words >= 20, "progress": f"{min(today_words, 20)}/20"},
            {"id": 4, "label": "Earn 50 XP", "done": today_xp >= 50, "progress": f"{min(today_xp, 50)}/50"},
            {"id": 5, "label": "80%+ accuracy", "done": today_accuracy >= 80, "progress": f"{today_accuracy}%" if today_total_q > 0 else ""},
            {"id": 6, "label": "Login streak +1", "done": streak_days >= 1, "progress": ""},
        ]

        return {
            "total_xp": total_xp,
            "total_coins": total_coins,
            "total_lessons": total_lessons,
            "total_defeated": total_lessons,
            "total_words_typed": total_words,
            "total_time_seconds": total_time,
            "today_time_seconds": today_time,
            "today_words": today_words,
            "today_missions": today_missions,
            "achievements": {
                "unlocked": 0,
                "total": 0,
            },
            "streak_days": streak_days,
        }

    @staticmethod
    def _calc_streak_days(records: list) -> int:
        """从已完成的记录中计算连续学习天数"""
        dates = set()
        for r in records:
            dt_str = r.get("completed_at", "")
            if dt_str:
                try:
                    d = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).date()
                    dates.add(d)
                except (ValueError, TypeError):
                    continue

        if not dates:
            return 0

        today = date.today()
        streak = 0
        check_date = today

        while check_date in dates:
            streak += 1
            check_date -= timedelta(days=1)

        return streak

    @staticmethod
    def get_history(user_id: str, app_code: str) -> dict:
        supabase = get_supabase_client()

        today = date.today()
        seven_days_ago = today - timedelta(days=6)
        seven_days_ago_iso = datetime.combine(seven_days_ago, datetime.min.time()).replace(tzinfo=timezone.utc).isoformat()

        # 所有 records
        records_resp = (
            supabase.table("lesson_records")
            .select("xp_earned, coins_earned, total_questions, correct_count, wrong_count, time_seconds, lesson_id, completed_at")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .execute()
        )

        all_records = records_resp.data or []

        # 总计
        total_xp = sum(r.get("xp_earned", 0) or 0 for r in all_records)
        total_coins = sum(r.get("coins_earned", 0) or 0 for r in all_records)
        total_time = sum(r.get("time_seconds", 0) or 0 for r in all_records)
        streak_days = StatsService._calc_streak_days(all_records)

        # 近 7 天聚合
        daily_map = {}
        for i in range(7):
            d = seven_days_ago + timedelta(days=i)
            daily_map[d] = {"xp": 0, "coins": 0, "missions": 0, "records": []}

        for r in all_records:
            dt_str = r.get("completed_at", "")
            if not dt_str:
                continue
            try:
                d = datetime.fromisoformat(dt_str.replace("Z", "+00:00")).date()
            except (ValueError, TypeError):
                continue
            if d in daily_map:
                daily_map[d]["xp"] += r.get("xp_earned", 0) or 0
                daily_map[d]["coins"] += r.get("coins_earned", 0) or 0
                daily_map[d]["records"].append(r)

        daily_activity = []
        for i in range(7):
            d = seven_days_ago + timedelta(days=i)
            dm = daily_map[d]
            missions_done = 0
            day_records = dm["records"]
            if day_records:
                day_correct = sum(rr.get("correct_count", 0) or 0 for rr in day_records)
                day_total_q = sum(rr.get("total_questions", 0) or 0 for rr in day_records)
                day_time = sum(rr.get("time_seconds", 0) or 0 for rr in day_records)
                day_xp = dm["xp"]
                day_accuracy = round(day_correct / day_total_q * 100) if day_total_q > 0 else 0

                if len(day_records) >= 1: missions_done += 1
                if day_time >= 600: missions_done += 1
                if day_total_q >= 20: missions_done += 1
                if day_xp >= 50: missions_done += 1
                if day_accuracy >= 80: missions_done += 1
                if streak_days >= 1 and d == today: missions_done += 1

            daily_activity.append({
                "date": d.strftime("%m/%d"),
                "xp": dm["xp"],
                "coins": dm["coins"],
                "missions": missions_done,
            })

        # 最近学习记录
        recent_raw = all_records[:20]

        # 批量查 lesson + course 信息
        lesson_ids = list({r["lesson_id"] for r in recent_raw if r.get("lesson_id")})
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

        recent_lessons = []
        for r in recent_raw:
            lid = r.get("lesson_id", "")
            info = lesson_map.get(lid, {})
            correct = r.get("correct_count", 0) or 0
            wrong = r.get("wrong_count", 0) or 0
            total_q = correct + wrong
            accuracy = round(correct / total_q * 100) if total_q > 0 else 0

            recent_lessons.append({
                "lesson_id": lid,
                "title": info.get("title", ""),
                "course_name": info.get("course_name", ""),
                "correct_count": correct,
                "wrong_count": wrong,
                "accuracy": accuracy,
                "xp_earned": r.get("xp_earned", 0) or 0,
                "time_seconds": r.get("time_seconds", 0) or 0,
                "completed_at": r.get("completed_at", ""),
            })

        return {
            "total_xp": total_xp,
            "total_coins": total_coins,
            "total_time_seconds": total_time,
            "streak_days": streak_days,
            "daily_activity": daily_activity,
            "recent_lessons": recent_lessons,
        }
