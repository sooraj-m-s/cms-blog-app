from fastapi import APIRouter, Depends, UploadFile, Form, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.services.blog_service import BlogService
from app.dependencies import get_current_admin as ca
from app.services.admin_service import AdminService


router = APIRouter()

@router.get("/landing/")
def get_landing_page(db: Session = Depends(get_db), current_user: User = Depends(ca)):
    blog_service = BlogService(db)
    return {"blogs": blog_service.get_all_blogs()}


@router.patch("/blogs/{blog_id}")
def update_blog(blog_id: int, title: str = Form(None), content: str = Form(None), image: UploadFile = File(None), db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.update_blog(blog_id, title, content, image)

