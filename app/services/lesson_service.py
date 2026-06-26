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

        # 查旧记录（每人每 lesson 最多一条）
        old_resp = (
            supabase.table("lesson_records")
            .select("id, correct_count, wrong_count, xp_earned, coins_earned")
            .eq("user_id", user_id)
            .eq("lesson_id", lesson_id)
            .limit(1)
            .execute()
        )

        old_record = old_resp.data[0] if old_resp.data else None

        # 检查已有记录：准确率 ≥ 50% 则拒绝
        if old_record:
            old_total = (old_record.get("correct_count", 0) or 0) + (old_record.get("wrong_count", 0) or 0)
            old_accuracy = old_record.get("correct_count", 0) / old_total if old_total > 0 else 0
            if old_accuracy >= 0.5:
                raise AppException(code=400, message="Lesson already passed, no rewards available")

        # 计算本次奖励
        xp_new, coins_new = _calc_reward(correct_count, wrong_count)
        now = datetime.now(timezone.utc).isoformat()

        if old_record:
            # retry：更新记录，补 XP/Coin 差值
            xp_old = old_record.get("xp_earned", 0) or 0
            coins_old = old_record.get("coins_earned", 0) or 0
            xp_delta = xp_new - xp_old
            coins_delta = coins_new - coins_old

            supabase.table("lesson_records").update({
                "correct_count": correct_count,
                "wrong_count": wrong_count,
                "total_questions": total_questions,
                "time_seconds": time_seconds,
                "xp_earned": xp_new,
                "coins_earned": coins_new,
                "completed_at": now,
            }).eq("id", old_record["id"]).execute()
        else:
            # 首次：插入新记录，全部算奖励
            xp_delta = xp_new
            coins_delta = coins_new

            supabase.table("lesson_records").insert({
                "user_id": user_id,
                "lesson_id": lesson_id,
                "correct_count": correct_count,
                "wrong_count": wrong_count,
                "total_questions": total_questions,
                "time_seconds": time_seconds,
                "xp_earned": xp_new,
                "coins_earned": coins_new,
                "completed_at": now,
            }).execute()

        # 更新 auth_users
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
        new_xp_total = current_xp + xp_delta
        new_coins_total = current_coins + coins_delta

        supabase.table("auth_users").update({
            "total_xp": new_xp_total,
            "coins": new_coins_total,
        }).eq("id", user_id).execute()

        # 更新 user_lesson_progress
        progress_resp = (
            supabase.table("user_lesson_progress")
            .select("id, finish_count")
            .eq("user_id", user_id)
            .eq("lesson_id", lesson_id)
            .limit(1)
            .execute()
        )

        if progress_resp.data:
            prev = progress_resp.data[0]
            new_best = max(correct_count, prev.get("best_score", 0) or 0)
            supabase.table("user_lesson_progress").update({
                "is_completed": True,
                "best_score": new_best,
                "finish_count": (prev.get("finish_count", 0) or 0) + 1,
                "last_finished_at": now,
            }).eq("id", prev["id"]).execute()
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
            "xp_earned": xp_delta,
            "coins_earned": coins_delta,
            "total_xp": new_xp_total,
            "lesson_status": "completed",
            "next_lesson_status": next_lesson_status,
        }
