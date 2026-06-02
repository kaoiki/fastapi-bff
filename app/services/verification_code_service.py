import random
from datetime import datetime, timedelta, timezone

from app.core.config import settings
from app.stores.verification_code_store import VerificationCodeStore
from app.utils.email_util import send_verification_email
from app.core.exceptions import AppException


class VerificationCodeService:

    @staticmethod
    def send_code(app_code: str, email: str, biz_type: str):
        existing = VerificationCodeStore.get_valid_code(app_code, email, biz_type)

        if existing:
            expires_at = datetime.fromisoformat(existing["expires_at"])
            now = datetime.now(timezone.utc)

            remaining = int((expires_at - now).total_seconds())
            minutes = max(1, remaining // 60)

            raise AppException(
                message=f"Code already sent. Please check your email or try again in {minutes} minutes.",
                code=400
            )

        code = str(random.randint(100000, 999999))

        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=settings.verification_code_ttl_seconds)

        VerificationCodeStore.insert({
            "app_code": app_code,
            "email": email,
            "code": code,
            "biz_type": biz_type,
            "expires_at": expires_at.isoformat(),
            "status": 1
        })

        send_verification_email(
            to_email=email,
            code=code,
            app_code=app_code
        )

    @staticmethod
    def verify_code(app_code: str, email: str, biz_type: str, code: str):
        record = VerificationCodeStore.get_valid_code(app_code, email, biz_type)

        if not record:
            raise AppException(
                message="Invalid or expired code.",
                code=400
            )

        if record["code"] != code:
            raise AppException(
                message="Invalid code.",
                code=400
            )

        VerificationCodeStore.mark_used(record["id"])
        return record