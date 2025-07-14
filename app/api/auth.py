from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.config import get_db
from app.schemas.user_schema import UserRegister, UserLogin
from app.services.user_service import UserService
from fastapi.security import OAuth2PasswordBearer
from app.core.config import SECRET_KEY
from app.models.user import User
import jwt


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


async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

