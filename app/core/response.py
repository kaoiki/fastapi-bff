from typing import Any, Optional

from app.schemas.common import ApiResponse


def success(data: Optional[Any] = None, message: str = "success") -> ApiResponse:
    return ApiResponse(
        code=0,
        message=message,
        data=data if data is not None else {}
    )


def fail(code: int = 1, message: str = "error", data: Any = None) -> ApiResponse:
    return ApiResponse(
        code=code,
        message=message,
        data=data
    )