
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


# -------------------------
# Enrollment
# -------------------------

class EnrollmentCreate(BaseModel):
    employee_id: int
    course_id: int
    actor: str = "employee"


# -------------------------
# Course Completion
# -------------------------

class CompletionCreate(BaseModel):
    score: Decimal | None = Field(default=None, ge=0, le=100)
    outcome: str = Field(
        default="ATTENDED",
        pattern="^(ATTENDED|PASSED|FAILED)$",
    )
    certificate_url: str | None = None
    actor: str = "manager"


# -------------------------
# Skill Assessment
# -------------------------

class AssessmentCreate(BaseModel):
    level: int = Field(ge=0, le=5)
    assessor: str = "manager"
    source: str = "MANUAL"
    notes: str | None = None


# -------------------------
# Authentication
# -------------------------

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class UserCreate(BaseModel):
    email: EmailStr
    full_name: str = Field(min_length=2, max_length=150)
    password: str = Field(min_length=12, max_length=128)
    role: str = Field(
        pattern="^(Admin|Manager|Employee)$"
    )
    employee_id: int | None = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: str
    role: str
    employee_id: int | None
    is_active: bool

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse
