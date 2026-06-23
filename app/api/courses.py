from fastapi import APIRouter, Depends

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.services.courses_service import CoursesService

router = APIRouter(prefix="/api", tags=["courses"])


@router.get("/courses")
def list_courses(
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = CoursesService.list_courses(
        app_code=app_code,
        user_id=current_user["id"],
    )
    return success(data=data)


@router.get("/courses/{course_id}/lessons")
def list_lessons(
    course_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = CoursesService.list_lessons(
        app_code=app_code,
        user_id=current_user["id"],
        course_id=course_id,
    )
    return success(data=data)


@router.post("/courses/{course_id}/enroll")
def enroll_course(
    course_id: str,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    CoursesService.enroll(
        app_code=app_code,
        user_id=current_user["id"],
        course_id=course_id,
    )
    return success()
