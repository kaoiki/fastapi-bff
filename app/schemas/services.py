from typing import Optional

from pydantic import BaseModel, Field


CATEGORIES = [
    "walking", "veterinary", "boarding",
    "grooming", "lost_found", "meetup", "other",
]

FEE_TYPES = ["free", "negotiable", "paid"]


class CreateServiceRequest(BaseModel):
    category: str = Field(..., min_length=1)
    title: str = Field(..., min_length=1, max_length=100)
    description: str = Field(..., min_length=1)
    contact_phone: Optional[str] = None
    contact_wechat: Optional[str] = None
    service_area: Optional[str] = None
    available_time: Optional[str] = None
    fee_type: str = "free"
    provider_image: Optional[str] = None


class UpdateServiceRequest(BaseModel):
    category: Optional[str] = None
    title: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    contact_phone: Optional[str] = None
    contact_wechat: Optional[str] = None
    service_area: Optional[str] = None
    available_time: Optional[str] = None
    fee_type: Optional[str] = None
    provider_image: Optional[str] = None


class VoteRequest(BaseModel):
    vote: int
