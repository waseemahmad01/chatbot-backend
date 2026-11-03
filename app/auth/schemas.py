from pydantic import BaseModel, EmailStr, ConfigDict
from app.db.models import User

class RegisterUser(BaseModel):
    email: EmailStr
    password: str
    confirm_password: str

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    email: EmailStr

class LoginUserRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"

class LoginUser(BaseModel):
    user: UserResponse
    access_token: str