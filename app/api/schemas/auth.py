from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=1, max_length=200)


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str


class UserResponse(BaseModel):
    id: int
    email: str


class StatsResponse(BaseModel):
    email: str
    trial_active: bool
    trial_days_remaining: int
    trial_expires_at: str
    documents_count: int
    queries_count: int
    pii_events_count: int
