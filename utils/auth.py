import jwt
from fastapi import HTTPException, Request
from datetime import datetime, timedelta, timezone
from typing import Union, Any, Optional
from fastapi.security import HTTPBearer
from jose import jwt, JWTError
from .config import settings

def create_access_token(subject: Union[str, Any], role: str, expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject), "role": role}
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, settings.algorithm)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any], expires_delta: int = None):
    if expires_delta is not None:
        expires_delta = datetime.now(tz=timezone.utc) + expires_delta
    else:
        expires_delta = datetime.now(tz=timezone.utc) + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    
    to_encode = {"exp": expires_delta, "sub": str(subject)}
    encoded_jwt = jwt.encode(to_encode, settings.refresh_secret_key, settings.algorithm)
    return encoded_jwt

def decodeJWT(jwtoken: str):
    try:
        payload = jwt.decode(jwtoken, settings.secret_key, settings.algorithm)
        return payload
    except JWTError:
        return None


class JWTBearer(HTTPBearer):
    def __init__(self, allowed_roles: Optional[list] = None, auto_error: bool = True):
        super(JWTBearer, self).__init__(auto_error=auto_error)
        self.allowed_roles = allowed_roles

    async def __call__(self, request: Request) -> Optional[str]:
        token = request.cookies.get("access_token")
        if not token:
            raise HTTPException(status_code=403, detail="Not authenticated")

        payload = decodeJWT(token)

        if not payload:
            raise HTTPException(status_code=403, detail="Invalid or expired token")

        # Check if the user's role is allowed
        user_role = payload.get("role")
        if self.allowed_roles and user_role not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="Access forbidden: insufficient permissions")

        return token

    def verify_jwt(self, jwtoken: str) -> bool:
        try:
            payload = decodeJWT(jwtoken)
            return True
        except jwt.ExpiredSignatureError:
            return False
        except jwt.JWTError:
            return False