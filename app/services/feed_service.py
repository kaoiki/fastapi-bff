from app.services.supabase import get_supabase_client


class FeedService:

    @staticmethod
    def get_feed(user_id: str, app_code: str, page: int = 1, page_size: int = 10) -> tuple:
        supabase = get_supabase_client()
        offset = (page - 1) * page_size
        limit = page_size

        # lesson_records（type=lesson）
        lessons_resp = (
            supabase.table("lesson_records")
            .select("correct_count, wrong_count, total_questions, time_seconds, xp_earned, coins_earned, lesson_id, completed_at")
            .eq("user_id", user_id)
            .order("completed_at", desc=True)
            .limit(50)
            .execute()
        )

        # 查 lesson → course 映射
        lesson_ids = list({r["lesson_id"] for r in (lessons_resp.data or []) if r.get("lesson_id")})
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
                    "name": l["name"],
                    "course": course_map.get(l["course_id"], ""),
                }

        # lesson 事件
        events = []
        for r in (lessons_resp.data or []):
            info = lesson_map.get(r["lesson_id"], {})
            correct = r.get("correct_count", 0) or 0
            wrong = r.get("wrong_count", 0) or 0
            total = correct + wrong
            accuracy = round(correct / total * 100) if total > 0 else 0
            events.append({
                "type": "lesson",
                "title": f"Completed {info.get('name', '')}",
                "detail": f"{info.get('course', '')} · {accuracy}% · {r.get('time_seconds', 0)}s",
                "xp": r.get("xp_earned", 0) or 0,
                "coins": r.get("coins_earned", 0) or 0,
                "icon": "stadia_controller",
                "created_at": r.get("completed_at", ""),
            })

        # checkins（type=checkin）
        checkins_resp = (
            supabase.table("checkins")
            .select("created_at, type")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(50)
            .execute()
        )

        # 计算 streak（取最近 checkin 时顺便算一下天数）
        all_checkin_dates = sorted(
            [r["created_at"][:10] for r in (checkins_resp.data or []) if r.get("created_at")],
            reverse=True
        )
        streak = 0
        from datetime import date, timedelta
        today = date.today()
        check = today
        for d_str in all_checkin_dates:
            try:
                d = date.fromisoformat(d_str)
                if d == check:
                    streak += 1
                    check -= timedelta(days=1)
                elif d < check:
                    break
            except (ValueError, TypeError):
                continue

        for r in (checkins_resp.data or []):
            events.append({
                "type": "checkin",
                "title": "Daily check-in",
                "detail": f"Day {streak} streak" if streak > 0 else "Daily check-in",
                "xp": 0,
                "coins": 0,
                "icon": "edit_calendar",
                "created_at": r.get("created_at", ""),
            })

        # achievements（type=achievement）
        ach_resp = (
            supabase.table("user_achievements")
            .select("achievement_id, unlocked_at")
            .eq("user_id", user_id)
            .eq("app_code", app_code)
            .order("unlocked_at", desc=True)
            .limit(50)
            .execute()
        )

        ach_ids = [r["achievement_id"] for r in (ach_resp.data or []) if r.get("achievement_id")]
        ach_name_map = {}
        ach_desc_map = {}
        ach_reward_map = {}
        if ach_ids:
            a_resp = (
                supabase.table("achievements")
                .select("id, title, description, reward_coins")
                .in_("id", ach_ids)
                .execute()
            )
            for a in (a_resp.data or []):
                ach_name_map[a["id"]] = a["title"]
                ach_desc_map[a["id"]] = a.get("description", "")
                ach_reward_map[a["id"]] = a.get("reward_coins", 0)

        for r in (ach_resp.data or []):
            aid = r["achievement_id"]
            events.append({
                "type": "achievement",
                "title": f"Unlocked: {ach_name_map.get(aid, '')}",
                "detail": ach_desc_map.get(aid, ""),
                "xp": 0,
                "coins": ach_reward_map.get(aid, 0),
                "icon": "workspace_premium",
                "created_at": r.get("unlocked_at", ""),
            })

        # 合并排序
        events.sort(key=lambda e: e.get("created_at", ""), reverse=True)

        total = len(events)
        page_events = events[offset:offset + limit]

        return page_events, total
