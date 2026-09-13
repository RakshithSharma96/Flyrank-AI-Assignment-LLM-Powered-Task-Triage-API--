from enum import Enum

from pydantic import BaseModel, Field


class Category(str, Enum):
    work = "work"
    study = "study"
    personal = "personal"
    admin = "admin"
    other = "other"


class Urgency(str, Enum):
    low = "low"
    normal = "normal"
    high = "high"


class TriageRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=2000)


class TriageResponse(BaseModel):
    category: Category
    urgency: Urgency
    confidence: float = Field(..., ge=0.0, le=1.0)
    reason: str = Field(..., min_length=1)