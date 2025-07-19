from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import jwt
from app.models.user import User
from app.models.blog import Blog
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
        blogs = self.db.query(Blog).all()
        return [{"id": blog.id, "title": blog.title, "content": blog.content, "image_url": blog.image_url,
                 "read_count": blog.read_count, "created_at": blog.created_at, "updated_at": blog.updated_at}
                for blog in blogs]


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

