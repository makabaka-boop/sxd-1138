from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models import User
from app.enums import UserRole
from app.schemas import TokenData
from app.logger import logger

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def get_user(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username, User.is_active == True).first()


def authenticate_user(db: Session, username: str, password: str) -> Optional[User]:
    user = get_user(db, username)
    if not user:
        logger.warning(f"登录失败: 用户不存在 - {username}")
        return None
    if not verify_password(password, user.hashed_password):
        logger.warning(f"登录失败: 密码错误 - {username}")
        return None
    logger.info(f"用户登录成功 - {username} ({user.role})")
    return user


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无法验证凭据",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="用户已被禁用")
    return current_user


def require_role(allowed_roles: list):
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role not in allowed_roles:
            logger.warning(f"权限不足: 用户 {current_user.username} 尝试访问需要 {allowed_roles} 权限的接口")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="权限不足"
            )
        return current_user
    return role_checker


require_admin = require_role([UserRole.ADMIN])
require_operator = require_role([UserRole.ADMIN, UserRole.OPERATOR])
require_inspector = require_role([UserRole.ADMIN, UserRole.INSPECTOR])
require_any_staff = require_role([UserRole.ADMIN, UserRole.OPERATOR, UserRole.INSPECTOR])
