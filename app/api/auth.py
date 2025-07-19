from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user_schema import UserRegister, Login
from app.services.user_service import UserService
from app.services.admin_service import AdminService
from fastapi.security import OAuth2PasswordBearer


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
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.logout_user(token, db)


@router.post("/admin/login/")
def admin_login(user: Login, db: Session = Depends(get_db)):
    admin_service = AdminService(db)
    return admin_service.admin_login_user(user.email, user.password)

