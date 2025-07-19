from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import jwt
from app.models.user import User
from app.models.blog import Blog
from app.models.feedback import Feedback
from app.core.config import SECRET_KEY
from passlib.context import CryptContext
from sqlalchemy.orm import Session


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class AdminService:
    def __init__(self, db: Session):
        self.db = db


    def admin_login_user(self, email: str, password: str):
        db_user = self.db.query(User).filter(User.email == email).first()
        if not db_user or not pwd_context.verify(password, db_user.password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not db_user.is_admin:
            raise HTTPException(status_code=403, detail="Admin access required")

        access_token_expires = timedelta(days=2)
        access_token = jwt.encode(
            {"sub": db_user.email, "id": db_user.id, "is_admin": True, "exp": datetime.now(timezone.utc) + access_token_expires},
            SECRET_KEY,
            algorithm="HS256"
        )
        return {"access_token": access_token, "token_type": "bearer"}


    def admin_get_all_blogs(self):
        blogs = self.db.query(Blog).filter(Blog.is_deleted == False).all()
        if not blogs:
            raise HTTPException(status_code=404, detail="No blogs found")
        return [{"id": blog.id, "title": blog.title, "content": blog.content, "image_url": blog.image_url,
                 "is_blocked": blog.is_blocked, "created_at": blog.created_at, "updated_at": blog.updated_at}
                for blog in blogs]


    def list_all_users(self):
        users = self.db.query(User).filter(User.is_admin == False).all()
        if not users:
            raise HTTPException(status_code=404, detail="No users found")
        return [{"id": user.id, "email": user.email, "is_blocked": user.is_blocked, "created_at": user.created_at}
                for user in users]


    def block_unblock_user(self, user_id: int):
        user = self.db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        user.is_blocked = not user.is_blocked
        self.db.commit()
        self.db.refresh(user)
        return {"message": f"User is_blocked toggled to {user.is_blocked}", "user_id": user.id}


    def update_blog(self, blog_id: int, title: str = None, content: str = None, image_url: str = None):
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")

        if title is not None:
            if self.db.query(Blog).filter(Blog.title == title, Blog.id != blog_id).first():
                raise HTTPException(status_code=400, detail="Blog title already exists")
            blog.title = title
        if content is not None:
            blog.content = content
        if image_url is not None:
            blog.image_url = image_url

        self.db.commit()
        self.db.refresh(blog)
        return {"message": "Blog updated successfully", "blog_id": blog.id}


    def block_unblock_blog(self, blog_id: int):
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        if blog.is_deleted:
            raise HTTPException(status_code=400, detail="Blog is deleted and cannot be blocked")

        blog.is_blocked = not blog.is_blocked
        self.db.commit()
        self.db.refresh(blog)
        return {"message": f"Blog is_blocked toggled to {blog.is_blocked}", "blog_id": blog.id}


    def toggle_feedback_listed(self, feedback_id: int):
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found")
        if feedback.is_deleted:
            raise HTTPException(status_code=400, detail="Feedback is deleted and cannot be toggled")

        feedback.is_listed = not feedback.is_listed
        self.db.commit()
        self.db.refresh(feedback)
        return {"message": f"Feedback is_listed toggled to {feedback.is_listed}", "feedback_id": feedback.id}

