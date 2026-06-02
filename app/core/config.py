from pathlib import Path
from typing import List

from dotenv import load_dotenv
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=ENV_PATH, override=True)


class Settings(BaseSettings):
    app_name: str = "FastAPI BFF"
    app_version: str = "0.1.0"
    debug: bool = True
    host: str = "127.0.0.1"
    port: int = 2248
    cors_allow_origins: str = "*"

    supabase_url: str = ""
    supabase_service_role_key: str = ""

    allowed_app_codes: str = ""

    verification_code_ttl_seconds: int = 300
    verification_code_length: int = 6
    token_ttl_seconds: int = 604800

    email_sender: str = ""
    email_password: str = ""
    email_smtp_host: str = ""
    email_smtp_port: int = 465
    email_use_ssl: bool = True

    email_register_code_subject: str = "[Heartbeat] Register Verification Code"
    email_reset_code_subject: str = "[Heartbeat] Reset Password Verification Code"

    def get_allowed_app_codes(self) -> List[str]:
        if not self.allowed_app_codes:
            return []
        return [code.strip() for code in self.allowed_app_codes.split(",") if code.strip()]

    model_config = SettingsConfigDict(
        case_sensitive=False
    )


settings = Settings()