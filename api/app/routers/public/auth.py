from fastapi import APIRouter, Depends
from app.core.dependencies import get_current_admin
from app.schemas import AdminLoginResponse, LoginRequest, LogoutResponse
from app.utils.auth import login_user, logout_user


router = APIRouter(tags=["auth"])


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(login_data: LoginRequest):
    """Логин через JSON"""
    return await login_user(login_data)


@router.post("/logout", response_model=LogoutResponse)
async def admin_logout(current_admin=Depends(get_current_admin)):
    """Логаут"""
    return await logout_user(current_admin)