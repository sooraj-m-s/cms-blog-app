from fastapi import Depends, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.config import SECRET_KEY
from app.db.database import get_db
from app.models.user import User
from app.models.logout import Logout
import jwt, logging


logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        revoked_token = db.query(Logout).filter(Logout.token == token).first()
        if revoked_token:
            raise HTTPException(status_code=401, detail="Unauthorized!")

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked, please contact support!")
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")


async def get_current_admin(request: Request, db: Session = Depends(get_db)):
    try:
        token = request.cookies.get("access_token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        revoked_token = db.query(Logout).filter(Logout.token == token).first()
        if revoked_token:
            raise HTTPException(status_code=401, detail="Unauthorized!")

        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        user = db.query(User).filter(User.email == email).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        if not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")
        return user
    except jwt.ExpiredSignatureError as e:
        logger.error(f"Unexpected errorrrrrr1: {e}")
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"Unexpected errorrrrrr2: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")
    except Exception as e:
        logger.error(f"Unexpected errorrrrrr3: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

