from sqlalchemy.orm import Session
from app.models.user import User
from passlib.context import CryptContext
from datetime import datetime, timedelta
from fastapi import HTTPException
from app.core.config import SECRET_KEY
import jwt


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def __init__(self, db: Session):
        self.db = db

    def register_user(self, user_data: dict):
        # Check if email already exists
        db_user = self.db.query(User).filter(User.email == user_data["email"]).first()
        if db_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        if len(user_data["password"]) < 8:
            raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
        if user_data["password"] != user_data["confirm_password"]:
            raise HTTPException(status_code=400, detail="Passwords do not match")

        # Hash the password
        hashed_password = pwd_context.hash(user_data["password"])

        # Create new user
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

    def login_user(self, email: str, password: str):
        db_user = self.db.query(User).filter(User.email == email).first()
        if not db_user or not pwd_context.verify(password, db_user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        # Generate JWT token
        access_token_expires = timedelta(minutes=30)  # Token expires in 30 minutes
        access_token = jwt.encode(
            {"sub": db_user.email, "id": db_user.id, "exp": datetime.utcnow() + access_token_expires},
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"access_token": access_token, "token_type": "bearer"}

