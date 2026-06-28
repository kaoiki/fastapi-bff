import math
from datetime import date, timedelta

from app.services.supabase import get_supabase_client
from app.services.checkin_service import CheckinService


def _calc_streak_from_checkins(records: list) -> int:
    dates = set()
    for r in records:
        dt_str = r.get("created_at", "")
        if dt_str:
            try:
                d = date.fromisoformat(dt_str[:10])
                dates.add(d)
            except (ValueError, TypeError):
                continue
    if not dates:
        return 0
    today = date.today()
    streak = 0
    check = today
    while check in dates:
        streak += 1
        check -= timedelta(days=1)
    return streak


class AchievementService:

    @staticmethod
    @staticmethod
    def list_public(app_code: str) -> list:
        supabase = get_supabase_client()
        ach_resp = (
            supabase.table("achievements")
            .select("*")
            .eq("app_code", app_code)
            .eq("status", 1)
            .order("id", desc=False)
            .execute()
        )
        return [
            {
                "id": a["id"],
                "title": a["title"],
                "description": a["description"],
                "category": a["category"],
                "icon": a["icon"],
                "target": a["target"],
                "reward_description": f"{a['reward_coins']} Coins" if a.get("reward_coins") else "",
            }
            for a in (ach_resp.data or [])
        ]

    @staticmethod
    def list_achievements(user_id: str, app_code: str) -> list:
        supabase = get_supabase_client()

        # 所有成就
        ach_resp = (
            supabase.table("achievements")
            .select("*")
            .eq("app_code", app_code)
            .eq("status", 1)
            .order("id", desc=False)
            .execute()
        )

        achievements = ach_resp.data or []

        # 用户已解锁
        unlocked_resp = (
            supabase.table("user_achievements")
            .select("achievement_id")
            .eq("user_id", user_id)
            .eq("app_code", app_code)
            .execute()
        )
        unlocked_ids = {r["achievement_id"] for r in (unlocked_resp.data or [])}

        # 统计数据
        stats = AchievementService._get_user_stats(user_id, app_code)

        result = []
        for ach in achievements:
            aid = ach["id"]
            current = AchievementService._calc_progress(aid, stats)
            result.append({
                "id": aid,
                "title": ach["title"],
                "description": ach["description"],
                "category": ach["category"],
                "icon": ach["icon"],
                "unlocked": aid in unlocked_ids,
                "current": current,
                "target": ach["target"],
                "reward_description": f"{ach['reward_coins']} Coins" if ach['reward_coins'] else "",
            })

        return result

    @staticmethod
    def check_new_achievements(user_id: str, app_code: str, lesson_id: str, course_id: str,
                                correct_count: int, wrong_count: int, time_seconds: int,
                                accuracy: float) -> list:
        supabase = get_supabase_client()

        # 已解锁的
        unlocked_resp = (
            supabase.table("user_achievements")
            .select("achievement_id")
            .eq("user_id", user_id)
            .eq("app_code", app_code)
            .execute()
        )
        already = {r["achievement_id"] for r in (unlocked_resp.data or [])}

        # 统计数据
        stats = AchievementService._get_user_stats(user_id, app_code)
        # 附加本次提交的临时数据
        stats["_current_course_id"] = course_id
        stats["_current_accuracy"] = accuracy
        stats["_current_time"] = time_seconds
        stats["_current_lesson_old_accuracy"] = AchievementService._get_old_accuracy(
            supabase, user_id, lesson_id
        )

        # 获取所有成就
        ach_resp = (
            supabase.table("achievements")
            .select("*")
            .eq("app_code", app_code)
            .eq("status", 1)
            .execute()
        )

        new_achievements = []
        total_reward = 0

        for ach in (ach_resp.data or []):
            aid = ach["id"]
            if aid in already:
                continue
            if AchievementService._check_condition(aid, stats):
                # 解锁
                supabase.table("user_achievements").insert({
                    "user_id": user_id,
                    "achievement_id": aid,
                    "app_code": app_code,
                }).execute()
                new_achievements.append({
                    "id": aid,
                    "title": ach["title"],
                    "description": ach["description"],
                    "reward_description": f"{ach['reward_coins']} Coins",
                })
                total_reward += ach.get("reward_coins", 0)

        # 发放金币
        if total_reward > 0:
            user_resp = (
                supabase.table("auth_users")
                .select("coins")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            current_coins = user_resp.data[0].get("coins", 0) if user_resp.data else 0
            supabase.table("auth_users").update({
                "coins": current_coins + total_reward,
            }).eq("id", user_id).execute()

        return new_achievements

    @staticmethod
    def _get_user_stats(user_id: str, app_code: str) -> dict:
        supabase = get_supabase_client()

        # lesson_records 汇总
        lr_resp = (
            supabase.table("lesson_records")
            .select("correct_count, wrong_count, total_questions, xp_earned, lesson_id")
            .eq("user_id", user_id)
            .execute()
        )
        records = lr_resp.data or []
        total_lessons = len(records)
        total_xp = sum(r.get("xp_earned", 0) or 0 for r in records)
        total_questions = sum(r.get("total_questions", 0) or 0 for r in records)
        accuracy_80_count = 0
        for r in records:
            c = r.get("correct_count", 0) or 0
            w = r.get("wrong_count", 0) or 0
            total = c + w
            if total > 0 and (c / total) >= 0.8:
                accuracy_80_count += 1

        # streak
        checkin_resp = (
            supabase.table("checkins")
            .select("created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        streak_days = _calc_streak_from_checkins(checkin_resp.data or [])
        total_checkins = len(checkin_resp.data or [])

        # 已完成的课程数（course complete）
        courses_completed = 0
        course_resp = (
            supabase.table("courses")
            .select("id")
            .eq("app_code", app_code)
            .eq("status", 1)
            .execute()
        )
        for course in (course_resp.data or []):
            lessons = (
                supabase.table("lessons")
                .select("id")
                .eq("course_id", course["id"])
                .eq("app_code", app_code)
                .eq("status", 1)
                .execute()
            )
            lesson_ids = [l["id"] for l in (lessons.data or [])]
            if not lesson_ids:
                continue
            prog = (
                supabase.table("user_lesson_progress")
                .select("lesson_id")
                .eq("user_id", user_id)
                .eq("app_code", app_code)
                .eq("is_completed", True)
                .in_("lesson_id", lesson_ids)
                .execute()
            )
            completed_ids = {p["lesson_id"] for p in (prog.data or [])}
            if set(lesson_ids).issubset(completed_ids):
                courses_completed += 1

        return {
            "total_lessons": total_lessons,
            "total_xp": total_xp,
            "total_questions": total_questions,
            "accuracy_80_count": accuracy_80_count,
            "streak_days": streak_days,
            "total_checkins": total_checkins,
            "courses_completed": courses_completed,
        }

    @staticmethod
    def _get_old_accuracy(supabase, user_id: str, lesson_id: str) -> float:
        r = (
            supabase.table("lesson_records")
            .select("correct_count, wrong_count")
            .eq("user_id", user_id)
            .eq("lesson_id", lesson_id)
            .limit(1)
            .execute()
        )
        if r.data:
            c = r.data[0].get("correct_count", 0) or 0
            w = r.data[0].get("wrong_count", 0) or 0
            total = c + w
            return c / total if total > 0 else 0
        return 0  # 没有旧记录

    @staticmethod
    def _calc_progress(aid: int, stats: dict) -> int:
        mapping = {
            1: stats.get("total_lessons", 0),
            2: stats.get("total_lessons", 0),
            3: stats.get("total_lessons", 0),
            4: stats.get("courses_completed", 0),
            5: 0,  # 特殊条件，无法量化进度
            6: 0,
            7: stats.get("accuracy_80_count", 0),
            8: stats.get("total_xp", 0),
            9: stats.get("total_xp", 0),
            10: stats.get("total_questions", 0),
            11: stats.get("total_questions", 0),
            12: 0,
            13: stats.get("streak_days", 0),
            14: stats.get("streak_days", 0),
            15: stats.get("total_checkins", 0),
            16: stats.get("total_checkins", 0),
        }
        return mapping.get(aid, 0)

    @staticmethod
    def _check_condition(aid: int, stats: dict) -> bool:
        mapping = {
            1: stats.get("total_lessons", 0) >= 1,
            2: stats.get("total_lessons", 0) >= 10,
            3: stats.get("total_lessons", 0) >= 25,
            4: stats.get("courses_completed", 0) >= 1,
            5: (stats.get("_current_lesson_old_accuracy", 1) < 0.5
                and stats.get("_current_accuracy", 0) >= 0.8),
            6: stats.get("_current_accuracy", 0) == 1.0,
            7: stats.get("accuracy_80_count", 0) >= 10,
            8: stats.get("total_xp", 0) >= 500,
            9: stats.get("total_xp", 0) >= 2000,
            10: stats.get("total_questions", 0) >= 100,
            11: stats.get("total_questions", 0) >= 1000,
            12: stats.get("_current_time", 999) <= 30,
            13: stats.get("streak_days", 0) >= 7,
            14: stats.get("streak_days", 0) >= 30,
            15: stats.get("total_checkins", 0) >= 1,
            16: stats.get("total_checkins", 0) >= 30,
        }
        return mapping.get(aid, False)
