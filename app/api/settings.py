from fastapi import APIRouter, Depends

from app.core.context import get_app_code
from app.core.dependencies import get_current_user_base
from app.core.response import fail, success
from app.schemas.settings import ChangePasswordRequest, DeleteAccountRequest, UpdateProfileRequest
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/api", tags=["settings"])


@router.get("/profile")
def get_profile(
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = SettingsService.get_profile(
        user_id=current_user["id"],
        app_code=app_code,
    )
    return success(data=data)


@router.put("/profile")
def update_profile(
    req: UpdateProfileRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    data = SettingsService.update_profile(
        user_id=current_user["id"],
        app_code=app_code,
        nickname=req.nickname,
        bio=req.bio,
    )
    return success(data=data)


@router.put("/auth/password/change")
def change_password(
    req: ChangePasswordRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    SettingsService.change_password(
        user_id=current_user["id"],
        app_code=app_code,
        current_password=req.current_password,
        new_password=req.new_password,
    )
    return success(message="Password updated successfully")


@router.delete("/account")
def delete_account(
    req: DeleteAccountRequest,
    app_code: str = Depends(get_app_code),
    current_user: dict = Depends(get_current_user_base),
):
    SettingsService.delete_account(
        user_id=current_user["id"],
        app_code=app_code,
        password=req.password,
    )
    return success(message="Account has been deactivated")
