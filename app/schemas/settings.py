from typing import Optional

from pydantic import BaseModel, Field


class UpdateProfileRequest(BaseModel):
    nickname: Optional[str] = Field(None, min_length=1)
    bio: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)


class DeleteAccountRequest(BaseModel):
    password: str
