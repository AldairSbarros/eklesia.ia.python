
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
import os
from app.ingestor import get_user_by_username, create_user
from fastapi import Request
from collections import defaultdict
import time

# Configurações
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 600

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    username: str
    email: str | None = None
    full_name: str | None = None
    disabled: bool | None = None


class UserInDB(User):
    hashed_password: str


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_user(username: str):
    user_db = get_user_by_username(username)
    if user_db:
        return UserInDB(
            username=user_db.username,
            email=user_db.email,
            full_name=user_db.full_name,
            disabled=bool(user_db.disabled),
            hashed_password=user_db.hashed_password
        )


def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(token_data.username)
    if user is None:
        raise credentials_exception
    return user


def register_user(username: str, email: str, full_name: str, password: str):
    hashed_password = pwd_context.hash(password)
    return create_user(username, email, full_name, hashed_password)


# --- Controle de requisições grátis por IP ---

# Limite de 10 requisições grátis por IP (reset a cada 24h)
FREE_LIMIT = 10
FREE_WINDOW = 60 * 60 * 24  # 24 horas
_ip_access = defaultdict(lambda: {"count": 0, "first": 0})
FREE_LIMIT = 10
FREE_WINDOW = 60 * 60 * 24  # 24 horas
_ip_access = defaultdict(lambda: {"count": 0, "first": 0})


def free_or_authenticated(
    request: Request,
    token: str = Depends(oauth2_scheme)
):
    # Se token JWT válido, libera
    if token:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            username: str = payload.get("sub")
            if username:
                return get_user(username)
        except Exception:
            pass
    # Se não tem token válido, verifica limite grátis por IP
    ip = request.client.host
    now = int(time.time())
    data = _ip_access[ip]
    if now - data["first"] > FREE_WINDOW:
        data["count"] = 0
        data["first"] = now
    if data["count"] < FREE_LIMIT:
        data["count"] += 1
        return None  # Usuário anônimo liberado
    raise HTTPException(
        status_code=401,
        detail="Limite grátis atingido. Faça login para continuar."
    )
