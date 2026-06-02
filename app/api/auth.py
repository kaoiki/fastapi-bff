from fastapi import APIRouter, Depends, Header
from app.schemas.auth import *
from app.services.auth_service import AuthService
from app.core.dependencies import get_current_user_base
from app.core.response import success
from app.services.user_service import UserService

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register/send-code")
def send_register_code(req: SendCodeRequest, x_app_code: str = Header(...)):
    AuthService.send_register_code(x_app_code, req.email)
    return {"code": 0, "message": "success"}


@router.post("/register")
def register(req: RegisterRequest, x_app_code: str = Header(...)):
    AuthService.register(x_app_code, req.email, req.password, req.code)
    return {"code": 0, "message": "success"}


@router.post("/login")
def login(req: LoginRequest, x_app_code: str = Header(...)):
    data = AuthService.login(x_app_code, req.email, req.password)
    return {"code": 0, "message": "success", "data": data}


@router.post("/password/send-code")
def send_reset_code(req: SendCodeRequest, x_app_code: str = Header(...)):
    AuthService.send_reset_code(x_app_code, req.email)
    return {"code": 0, "message": "success"}


@router.post("/password/reset")
def reset_password(req: ResetPasswordRequest, x_app_code: str = Header(...)):
    AuthService.reset_password(x_app_code, req.email, req.code, req.new_password)
    return {"code": 0, "message": "success"}


@router.put("/profile")
def update_profile(
    req: UpdateNicknameRequest,
    current_user: dict = Depends(get_current_user_base),
):
    """修改昵称"""
    UserService.update_nickname(current_user["id"], req.nickname)
    return success(data={"nickname": req.nickname.strip()})


@router.put("/password")
def change_password(
    req: ChangePasswordRequest,
    current_user: dict = Depends(get_current_user_base),
):
    """修改密码（已登录态，不需要验证码）"""
    UserService.change_password(current_user["id"], req.old_password, req.new_password)
    return success()