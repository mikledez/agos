from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field

class UserOut(BaseModel):
    id: int
    email: str
    name: str | None = None
    image: str | None = None
    email_verified: datetime | None = None
    created_at: datetime
    updated_at: datetime

class UserUpdate(BaseModel):
    name: str | None = None
    image: str | None = None

class SessionCreate(BaseModel):
    name: str = Field(min_length=1)
    parent_id: int | None = None

class SessionUpdate(BaseModel):
    name: str | None = None
    parent_id: int | None = None

class SessionOut(BaseModel):
    id: int
    user_id: int
    parent_id: int | None = None
    name: str
    created_at: datetime
    updated_at: datetime

class LegOut(BaseModel):
    hip_angle: float
    knee_angle: float
    ankle_angle: float
    feedback: str

class AnalyzeResponse(BaseModel):
    image_id: int
    session_id: int | None = None
    phase: str
    direction: str
    swing_leg: LegOut
    stance_leg: LegOut
    thigh_thigh_angle: float | None = None
    feedback: str
    annotated_image: str
    original_url: str
    annotated_url: str | None = None

class ImageOut(BaseModel):
    id: int
    session_id: int | None = None
    original_filename: str
    phase: str
    direction: str
    swing_hip: float | None = None
    swing_knee: float | None = None
    swing_ankle: float | None = None
    stance_hip: float | None = None
    stance_knee: float | None = None
    stance_ankle: float | None = None
    thigh_thigh: float | None = None
    feedback: str | None = None
    swing_feedback: str | None = None
    stance_feedback: str | None = None
    created_at: datetime
    updated_at: datetime
    original_url: str
    annotated_url: str | None = None

class ImageDetail(BaseModel):
    image: ImageOut
    humanization: "HumanizationOut | None" = None

class ImageUpdate(BaseModel):
    session_id: int | None = None
    phase: str | None = None
    direction: str | None = None

class HumanizationIn(BaseModel):
    model: str = Field(min_length=1)
    humanized_text: str = Field(min_length=1)
    prompt: str | None = None

class HumanizationUpdate(BaseModel):
    model: str | None = None
    prompt: str | None = None
    humanized_text: str | None = None

class HumanizationOut(BaseModel):
    id: int
    image_id: int
    model: str
    prompt: str | None = None
    humanized_text: str
    created_at: datetime
    updated_at: datetime

ImageDetail.model_rebuild()
