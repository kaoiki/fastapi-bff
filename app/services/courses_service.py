from datetime import datetime, timezone

from app.core.exceptions import AppException
from app.services.supabase import get_supabase_client


class CoursesService:

    @staticmethod
    def list_courses(app_code: str, user_id: str) -> list:
        supabase = get_supabase_client()

        courses_resp = (
            supabase.table("courses")
            .select("id, name, language_code, description, level, icon, author")
            .eq("app_code", app_code)
            .eq("status", 1)
            .order("sort", desc=False)
            .execute()
        )

        courses = courses_resp.data or []
        if not courses:
            return []

        course_ids = [c["id"] for c in courses]

        # 查 enrollment
        enroll_resp = (
            supabase.table("user_course_enrollments")
            .select("course_id")
            .eq("app_code", app_code)
            .eq("user_id", user_id)
            .in_("course_id", course_ids)
            .execute()
        )
        enrolled_ids = {r["course_id"] for r in (enroll_resp.data or [])}

        # 查 lessons
        lessons_resp = (
            supabase.table("lessons")
            .select("course_id, id")
            .eq("app_code", app_code)
            .eq("status", 1)
            .in_("course_id", course_ids)
            .execute()
        )

        lessons = lessons_resp.data or []
        course_lessons = {}
        for lesson in lessons:
            cid = lesson["course_id"]
            if cid not in course_lessons:
                course_lessons[cid] = []
            course_lessons[cid].append(lesson["id"])

        all_lesson_ids = [l["id"] for l in lessons]
        progress_map = {}

        if all_lesson_ids:
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
            is_enrolled = cid in enrolled_ids

            if not is_enrolled:
                status = "not_started"
                current_lesson = 0
            else:
                completed = sum(1 for lid in lesson_ids if progress_map.get(lid))
                if completed >= total_lessons:
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
                "author": course.get("author", "Platform"),
            })

        return result

    @staticmethod
    def list_lessons(app_code: str, user_id: str, course_id: str) -> list:
        supabase = get_supabase_client()

        lessons_resp = (
            supabase.table("lessons")
            .select("id, name, description, sort")
            .eq("app_code", app_code)
            .eq("course_id", course_id)
            .eq("status", 1)
            .order("sort", desc=False)
            .execute()
        )

        lessons = lessons_resp.data or []
        if not lessons:
            return []

        lesson_ids = [l["id"] for l in lessons]

        progress_resp = (
            supabase.table("user_lesson_progress")
            .select("lesson_id, is_completed")
            .eq("app_code", app_code)
            .eq("user_id", user_id)
            .in_("lesson_id", lesson_ids)
            .execute()
        )

        progress_map = {}
        for row in (progress_resp.data or []):
            progress_map[row["lesson_id"]] = row["is_completed"]

        result = []
        for i, lesson in enumerate(lessons):
            lid = lesson["id"]
            is_completed = progress_map.get(lid, False)

            if is_completed:
                status = "completed"
            elif i == 0 or progress_map.get(lessons[i - 1]["id"], False):
                status = "available"
            else:
                status = "locked"

            result.append({
                "id": lid,
                "title": lesson["name"],
                "description": lesson.get("description", ""),
                "sequence": i + 1,
                "status": status,
            })

        return result

    @staticmethod
    def enroll(app_code: str, user_id: str, course_id: str):
        supabase = get_supabase_client()

        # 确认课程存在
        course_resp = (
            supabase.table("courses")
            .select("id")
            .eq("id", course_id)
            .eq("app_code", app_code)
            .eq("status", 1)
            .limit(1)
            .execute()
        )

        if not course_resp.data:
            raise AppException(code=404, message="Course not found")

        # 幂等插入
        existing = (
            supabase.table("user_course_enrollments")
            .select("id")
            .eq("user_id", user_id)
            .eq("course_id", course_id)
            .limit(1)
            .execute()
        )

        if not existing.data:
            supabase.table("user_course_enrollments").insert({
                "user_id": user_id,
                "course_id": course_id,
                "app_code": app_code,
                "enrolled_at": datetime.now(timezone.utc).isoformat(),
            }).execute()
