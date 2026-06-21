from app.services.supabase import get_supabase_client


class CoursesService:

    @staticmethod
    def list_courses(app_code: str, user_id: str) -> list:
        supabase = get_supabase_client()

        # 获取所有课程
        courses_resp = (
            supabase.table("courses")
            .select("id, name, language_code, description, level, icon")
            .eq("app_code", app_code)
            .eq("status", 1)
            .order("sort", desc=False)
            .execute()
        )

        courses = courses_resp.data or []
        if not courses:
            return []

        course_ids = [c["id"] for c in courses]

        # 批量查每个课程的 lesson 总数
        lessons_resp = (
            supabase.table("lessons")
            .select("course_id, id")
            .eq("app_code", app_code)
            .eq("status", 1)
            .in_("course_id", course_ids)
            .execute()
        )

        lessons = lessons_resp.data or []

        # course_id → lesson 列表
        course_lessons = {}
        for lesson in lessons:
            cid = lesson["course_id"]
            if cid not in course_lessons:
                course_lessons[cid] = []
            course_lessons[cid].append(lesson["id"])

        # 查该用户在所有 lesson 上的进度
        all_lesson_ids = [l["id"] for l in lessons]
        progress_map = {}

        if all_lesson_ids and user_id:
            progress_resp = (
                supabase.table("user_lesson_progress")
                .select("lesson_id, is_completed")
                .eq("app_code", app_code)
                .eq("user_id", user_id)
                .in_("lesson_id", all_lesson_ids)
                .execute()
            )

            for row in (progress_resp.data or []):
                progress_map[row["lesson_id"]] = row["is_completed"]

        result = []
        for course in courses:
            cid = course["id"]
            lesson_ids = course_lessons.get(cid, [])
            total_lessons = len(lesson_ids)

            if total_lessons == 0 or not user_id:
                status = "not_started"
                current_lesson = 0
            else:
                completed = sum(1 for lid in lesson_ids if progress_map.get(lid))
                if completed == 0:
                    status = "not_started"
                    current_lesson = 0
                elif completed >= total_lessons:
                    status = "completed"
                    current_lesson = total_lessons
                else:
                    status = "learning"
                    current_lesson = completed

            result.append({
                "id": cid,
                "title": course["name"],
                "description": course.get("description", ""),
                "language": course.get("language_code", ""),
                "level": course.get("level", "Beginner"),
                "status": status,
                "total_lessons": total_lessons,
                "current_lesson": current_lesson,
                "icon": course.get("icon", "menu_book"),
            })

        return result
