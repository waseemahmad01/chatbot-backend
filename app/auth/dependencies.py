from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.sql.coercions import expect
from app.db.database import get_db
from app.db.models import User
from app.core.config import settings
import jwt

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db:Session = Depends(get_db)) -> User:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=["HS256"]
        )

    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

    except jwt.ExpiredTokenError:
        raise HTTPException(status_code=401, detail="Token expired")

    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal server error")

    user = db.query(User).filter(User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user