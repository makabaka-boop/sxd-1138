from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from app.database import get_db
from app.auth import authenticate_user, create_access_token, get_current_active_user
from app.config import settings
from app.schemas import Token, UserResponse
from app.logger import logger

router = APIRouter(prefix="/auth", tags=["认证"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires
    )
    logger.info(f"用户 {user.username} 登录成功")
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=UserResponse, summary="获取当前用户信息")
async def get_me(current_user = Depends(get_current_active_user)):
    return current_user
