from pydantic import BaseModel, Field


class LessonSubmitRequest(BaseModel):
    correct_count: int = Field(..., ge=0)
    wrong_count: int = Field(..., ge=0)
    total_questions: int = Field(..., ge=1)
    total_time_seconds: int = Field(..., ge=0)
