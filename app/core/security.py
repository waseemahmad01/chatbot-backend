from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.core.config import settings
from pwdlib.hashers.bcrypt import BcryptHasher


pwd = PasswordHash((BcryptHasher(),))


def hash_password(plain: str) -> str:
    return pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd.verify(plain, hashed)

def create_access_token(user_id: str) -> str:
    payload = {
        "sub": str(user_id),
        "exp": datetime.now(timezone.utc) + timedelta(days=settings.jwt_expiration_time)
    }

    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")