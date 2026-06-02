from app.core.exceptions import AppException
from app.services.user_service import UserService
from app.services.verification_code_service import VerificationCodeService
from app.services.session_token_service import SessionTokenService
from app.utils.password_util import verify_password


class AuthService:

    @staticmethod
    def register(app_code: str, email: str, password: str, code: str):
        if not password or len(password) < 6:
            raise AppException(message="Password must be at least 6 characters", code=400)

        if not code:
            raise AppException(message="Verification code is required", code=400)

        VerificationCodeService.verify_code(
            app_code=app_code,
            email=email,
            biz_type="register",
            code=code
        )

        if UserService.get_user(app_code, email):
            raise AppException(message="Email already registered", code=400)

        return UserService.create_user(app_code, email, password)

    @staticmethod
    def login(app_code: str, email: str, password: str):
        if not password:
            raise AppException(message="Password is required", code=400)

        user = UserService.get_user(app_code, email)
        if not user:
            raise AppException(message="Invalid email or password", code=400)

        if user["status"] == 0:
            raise AppException(message="Account is frozen", code=400)

        if user["status"] == 9:
            raise AppException(message="Account is deactivated", code=400)

        if not verify_password(password, user["password_hash"]):
            raise AppException(message="Invalid email or password", code=400)

        token_data = SessionTokenService.create_token(app_code, user["id"])

        return {
            "user_id": user["id"],
            "email": user["email"],
            "nickname": user["nickname"],
            "avatar": user["avatar"],
            "token": token_data["token"],
            "expires_at": token_data["expires_at"]
        }

    @staticmethod
    def send_register_code(app_code: str, email: str):
        user = UserService.get_user(app_code, email)
        if user:
            raise AppException(message="Email already registered", code=400)

        VerificationCodeService.send_code(
            app_code=app_code,
            email=email,
            biz_type="register"
        )

    @staticmethod
    def send_reset_code(app_code: str, email: str):
        user = UserService.get_user(app_code, email)
        if not user:
            raise AppException(message="Email not found", code=400)

        VerificationCodeService.send_code(
            app_code=app_code,
            email=email,
            biz_type="reset_password"
        )

    @staticmethod
    def reset_password(app_code: str, email: str, code: str, new_password: str):
        if not new_password or len(new_password) < 6:
            raise AppException(message="Password must be at least 6 characters", code=400)

        if not code:
            raise AppException(message="Verification code is required", code=400)

        user = UserService.get_user(app_code, email)
        if not user:
            raise AppException(message="Email not found", code=400)

        VerificationCodeService.verify_code(
            app_code=app_code,
            email=email,
            biz_type="reset_password",
            code=code
        )

        return UserService.reset_password(user["id"], new_password)