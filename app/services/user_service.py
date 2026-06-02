import random
import string

from app.core.exceptions import AppException
from app.stores.auth_user_store import AuthUserStore
from app.utils.password_util import hash_password


DEFAULT_AVATAR = "https://www.kaoiki.com/default.webp"


class UserService:

    @staticmethod
    def _generate_nickname(app_code: str) -> str:
        chars = string.ascii_letters + string.digits
        suffix = "".join(random.choices(chars, k=4))
        return f"{app_code.upper()}_{suffix}"

    @staticmethod
    def create_user(app_code: str, email: str, password: str):
        if not password or len(password) < 6:
            raise AppException(message="Password must be at least 6 characters", code=400)

        existing = AuthUserStore.get_by_email(app_code, email)
        if existing:
            raise AppException(message="Email already registered", code=400)

        password_hash = hash_password(password)
        nickname = UserService._generate_nickname(app_code)
        avatar = DEFAULT_AVATAR

        return AuthUserStore.create_user(
            app_code=app_code,
            email=email,
            password_hash=password_hash,
            nickname=nickname,
            avatar=avatar
        )

    @staticmethod
    def get_user(app_code: str, email: str):
        return AuthUserStore.get_by_email(app_code, email)

    @staticmethod
    def reset_password(user_id: str, new_password: str):
        if not new_password or len(new_password) < 6:
            raise AppException(message="Password must be at least 6 characters", code=400)

        password_hash = hash_password(new_password)
        return AuthUserStore.update_password(user_id, password_hash)