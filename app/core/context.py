from fastapi import Header

from app.core.config import settings
from app.core.exceptions import AppException


async def get_app_code(x_app_code: str = Header(..., alias="X-App-Code")) -> str:
    app_code = x_app_code.strip()

    if not app_code:
        raise AppException(code=400, message="X-App-Code header is required")

    allowed = settings.get_allowed_app_codes()

    if allowed and app_code not in allowed:
        raise AppException(code=403, message=f"app_code '{app_code}' is not allowed")

    return app_code