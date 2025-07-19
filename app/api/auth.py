from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.schemas.user_schema import UserRegister, UserLogin
from app.services.user_service import UserService
from fastapi.security import OAuth2PasswordBearer


router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

@router.post("/register/")
def register_user(user: UserRegister, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.register_user(user.dict())


@router.post("/login/")
def login(user: UserLogin, db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.login_user(user.email, user.password)

@router.post("/logout/")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user_service = UserService(db)
    return user_service.logout_user(token, db)

