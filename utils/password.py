from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def secure_pwd(raw_password):
    hashed = pwd_context.hash(raw_password)

    return hashed

def verify_pwd(plain, hash):
    return pwd_context.verify(plain, hash)