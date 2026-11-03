from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.auth.schemas import LoginUser, LoginUserRequest, TokenResponse, RegisterUser
from app.core.security import create_access_token, hash_password, verify_password
from app.db.database import get_db
from app.db.models import User



router = APIRouter()

@router.post("/register", response_model=TokenResponse, status_code=201)
def register(request:RegisterUser, db: Session = Depends(get_db)):
        existing = db.scalar(select(User).where(User.email == request.email))
        if existing:
            raise HTTPException(status_code=400, detail="User already exists with this email")
        if request.password != request.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        user = User(email = request.email, password_hash = hash_password(request.password))
        db.add(user)
        db.commit()
        db.refresh(user)
        return {"access_token": create_access_token(user.id), "token_type": "Bearer"}

@router.post("/login", response_model=LoginUser, status_code=200)
def login(request: LoginUserRequest, db: Session = Depends(get_db)):
    user = db.scalar(select(User).where(User.email == request.email))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return { "user":{"id": user.id, "email": user.email}, "access_token": create_access_token(user.id)}