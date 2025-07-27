from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from app.db.database import get_db
from app.schemas.user_schema import UserRegister, Login
from app.services.user_service import UserService
from app.services.admin_service import AdminService
from app.models.user import User
from app.dependencies import get_current_user as cu


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/register/")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.register_user(user.dict())


@router.post("/login/")
def login(user: Login, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.login_user(user.email, user.password)


@router.post("/logout/")
def logout(request: Request, db: Session = Depends(get_db),  current_user: User = Depends(cu)):
    token = request.cookies.get("access_token")
    user_service = UserService(db)
    return user_service.logout_user(token, db, current_user.id)


@router.post("/admin/login/")
def admin_login(user: Login, db: Session = Depends(get_db)):
    admin_service = AdminService(db)
    return admin_service.admin_login_user(user.email, user.password)


@router.post("/refresh/")
def refresh_token(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("refresh_token")
    user_service = UserService(db)
    return user_service.refresh_token(token, db)

