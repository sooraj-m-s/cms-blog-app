from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from app.core.config import SECRET_KEY
from app.models.user import User
from app.models.logout import Logout
import jwt, logging


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
access_token_expires = timedelta(minutes=15)
refresh_token_expires = timedelta(days=30)

class UserService:
    def __init__(self, db: Session):
        self.db = db


    def register_user(self, user_data: dict):
        try:
            db_user = self.db.query(User).filter(User.email == user_data["email"]).first()
            if db_user:
                raise HTTPException(status_code=400, detail="Email already registered")
            if len(user_data["password"]) < 8:
                raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
            if user_data["password"] != user_data["confirm_password"]:
                raise HTTPException(status_code=400, detail="Passwords do not match")

            hashed_password = pwd_context.hash(user_data["password"])
            new_user = User(
                full_name=user_data["full_name"],
                email=user_data["email"],
                password=hashed_password,
                created_at=datetime.now()
            )
            self.db.add(new_user)
            self.db.commit()
            self.db.refresh(new_user)

            return {"message": "User registered successfully", "user_id": new_user.id}
        except HTTPException as e:
            raise e
        except KeyError as e:
            logger.warning(f"Missing key in user_data: {e}")
            raise HTTPException(status_code=422, detail=f"Missing field: {e}")
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during user registration: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.error(f"Unexpected error during user registration: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def login_user(self, email: str, password: str):
        try:
            db_user = self.db.query(User).filter(User.email == email).first()
            if not db_user or not pwd_context.verify(password, db_user.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            if db_user.is_blocked:
                raise HTTPException(status_code=403, detail="Account is blocked, please contact support!")

            # Generate token
            access_token = jwt.encode(
                {"sub": db_user.email, "id": db_user.id, "exp": datetime.now(timezone.utc) + access_token_expires},
                SECRET_KEY,
                algorithm="HS256"
            )
            refresh_token = jwt.encode(
                {"sub": db_user.email, "id": db_user.id, "type": "refresh", "exp": datetime.now(timezone.utc) + refresh_token_expires},
                SECRET_KEY,
                algorithm="HS256"
            )

            response = JSONResponse(content={"message": "Login successful"})
            response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=access_token_expires, samesite="Lax", secure=False)
            response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=refresh_token_expires, samesite="Lax", secure=False)

            return response
        except HTTPException as e:  
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error during login for {email}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error during login for {email}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def logout_user(self, access_token: str, refresh_token: str, db: Session, user_id):
        try:
            revoked_access_token = Logout(token=access_token)
            revoked_refresh_token = Logout(token=refresh_token)
            db.add(revoked_access_token)
            db.add(revoked_refresh_token)
            db.commit()

            return {"message": "Logged out successfully"}
        except HTTPException as e:
            raise e
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except Exception as e:
            db.rollback()
            logger.exception(f"Unexpected error during logout: {e}")
            raise HTTPException(status_code=500, detail=f"Logout failed")


    def refresh_token(self, token_str: str, db: Session):
        try:
            # Verify refresh token
            payload = jwt.decode(token_str, SECRET_KEY, algorithms=["HS256"])
            email = payload.get("sub")
            if not email:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
            token_entry = db.query(Logout).filter(Logout.token == token_str).first()
            if token_entry:
                raise HTTPException(status_code=401, detail="Unauthorized!")
            exp_timestamp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
            if exp_timestamp < datetime.now(timezone.utc):
                raise HTTPException(status_code=401, detail="Refresh token expired")

            user = db.query(User).filter(User.email == email).first()
            if not user:
                raise HTTPException(status_code=401, detail="User not found")
            if user.is_blocked:
                raise HTTPException(status_code=403, detail="Account is blocked")

            # Generate new token
            new_access_token = jwt.encode(
                {"sub": user.email, "id": user.id, "exp": datetime.now(timezone.utc) + access_token_expires},
                SECRET_KEY,
                algorithm="HS256"
            )
            new_refresh_token = jwt.encode(
                {"sub": user.email, "id": user.id, "type": "refresh", "exp": datetime.now(timezone.utc) + refresh_token_expires},
                SECRET_KEY,
                algorithm="HS256"
            )

            response = JSONResponse(content={"message": "Token refreshed successfully"})
            response.set_cookie(key="access_token", value=new_access_token, httponly=True, max_age=access_token_expires, secure=False, samesite="lax")
            response.set_cookie(key="refresh_token", value=new_refresh_token, httponly=True, max_age=refresh_token_expires, secure=False, samesite="lax")

            return response
        except HTTPException as e:
            raise e
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Refresh token expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Database error during token refresh: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            db.rollback()
            logger.exception(f"Unexpected error during token refresh: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

