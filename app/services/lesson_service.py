from datetime import datetime, timezone

from app.core.exceptions import AppException
from app.services.supabase import get_supabase_client


def _calc_reward(correct: int, wrong: int) -> tuple:
    total = correct + wrong
    if total == 0:
        return 0, 0

    accuracy = correct / total
    accuracy_bonus = 20 if accuracy >= 0.8 else (10 if accuracy >= 0.5 else 0)
    xp = correct * 10 + accuracy_bonus
    coins = correct * 2
    return xp, coins


class LessonService:

    @staticmethod
    def submit(app_code: str, user_id: str, lesson_id: str, correct_count: int, wrong_count: int, total_questions: int, time_seconds: int) -> dict:
        supabase = get_supabase_client()

        # 确认 lesson 存在
        lesson_resp = (
            supabase.table("lessons")
            .select("id, course_id, sort")
            .eq("id", lesson_id)
            .eq("app_code", app_code)
            .eq("status", 1)
            .limit(1)
            .execute()
        )

        if not lesson_resp.data:
            raise AppException(code=400, message="Lesson not found")

        lesson = lesson_resp.data[0]

        # 查是否已学过
        progress_resp = (
            supabase.table("user_lesson_progress")
            .select("is_completed")
            .eq("user_id", user_id)
            .eq("lesson_id", lesson_id)
            .limit(1)
            .execute()
        )

        already_completed = progress_resp.data and progress_resp.data[0].get("is_completed")

        if already_completed:
            # 再次学习：不发奖励，不写记录
            user_r = supabase.table("auth_users").select("total_xp").eq("id", user_id).limit(1).execute()
            current_xp = user_r.data[0].get("total_xp", 0) if user_r.data else 0
            return {
                "xp_earned": 0,
                "coins_earned": 0,
                "total_xp": current_xp,
                "lesson_status": "completed",
                "next_lesson_status": None,
            }

        # 计算奖励
        xp_earned, coins_earned = _calc_reward(correct_count, wrong_count)
        now = datetime.now(timezone.utc).isoformat()

        # 写入 lesson_records
        supabase.table("lesson_records").insert({
            "user_id": user_id,
            "lesson_id": lesson_id,
            "correct_count": correct_count,
            "wrong_count": wrong_count,
            "total_questions": total_questions,
            "time_seconds": time_seconds,
            "xp_earned": xp_earned,
            "coins_earned": coins_earned,
            "completed_at": now,
        }).execute()

        # 更新 auth_users：读取当前值 + 累加
        user_resp = (
            supabase.table("auth_users")
            .select("total_xp, coins")
            .eq("id", user_id)
            .limit(1)
            .execute()
        )

        user_data = user_resp.data[0] if user_resp.data else {}
        current_xp = user_data.get("total_xp", 0) or 0
        current_coins = user_data.get("coins", 0) or 0
        new_xp = current_xp + xp_earned
        new_coins = current_coins + coins_earned

        supabase.table("auth_users").update({
            "total_xp": new_xp,
            "coins": new_coins,
        }).eq("id", user_id).execute()

        # 更新 user_lesson_progress
        existing_progress = (
            supabase.table("user_lesson_progress")
            .select("id, finish_count")
            .eq("user_id", user_id)
            .eq("lesson_id", lesson_id)
            .limit(1)
            .execute()
        )

        if existing_progress.data:
            supabase.table("user_lesson_progress").update({
                "is_completed": True,
                "best_score": correct_count,
                "finish_count": existing_progress.data[0].get("finish_count", 0) + 1,
                "last_finished_at": now,
            }).eq("id", existing_progress.data[0]["id"]).execute()
        else:
            supabase.table("user_lesson_progress").insert({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "app_code": app_code,
                "is_completed": True,
                "best_score": correct_count,
                "finish_count": 1,
                "last_finished_at": now,
            }).execute()

        # 查下一课状态
        next_lesson_status = None
        next_resp = (
            supabase.table("lessons")
            .select("id")
            .eq("course_id", lesson["course_id"])
            .eq("app_code", app_code)
            .eq("status", 1)
            .eq("sort", lesson["sort"] + 1)
            .limit(1)
            .execute()
        )
        if next_resp.data:
            next_lesson_status = "available"

        return {
            "xp_earned": xp_earned,
            "coins_earned": coins_earned,
            "total_xp": new_xp,
            "lesson_status": "completed",
            "next_lesson_status": next_lesson_status,
        }
