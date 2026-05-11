from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from api.config import settings
from db.database import get_db
from db.models import User

security = HTTPBearer()


def _decode_user(token: str, db: Session) -> User:
    try:
        payload = jwt.decode(token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm])
        user_id: str = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    return _decode_user(credentials.credentials, db)


def get_user_by_token(token: str, db: Session) -> User:
    """Validate a bare JWT string — used by SSE endpoints where EventSource cannot send headers."""
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return _decode_user(token, db)
