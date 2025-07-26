from fastapi import APIRouter, Depends, UploadFile, Form, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.user import User
from app.dependencies import get_current_admin as ca
from app.services.admin_service import AdminService


router = APIRouter()

@router.get("/landing/")
def get_landing_page(page: int = 1, page_size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.admin_get_all_blogs(page, page_size)


@router.get("/list-users/")
def list_all_users(page: int = 1, page_size: int = 10, db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.list_all_users(page, page_size)


@router.patch("/block-unblock-user/{user_id}")
def block_unblock_user(user_id: int, db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.block_unblock_user(user_id)


@router.patch("/blogs/{blog_id}")
def update_blog(blog_id: int, title: str = Form(None), content: str = Form(None), image: UploadFile = File(None), db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.update_blog(blog_id, title, content, image)


@router.patch("/blogs/{blog_id}/block/")
def block_blog(blog_id: int, db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.block_unblock_blog(blog_id)


@router.patch("/feedbacks/{blog_id}/")
def get_feedbacks(blog_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.get_feedbacks(blog_id, page, page_size)


@router.patch("/feedbacks/{feedback_id}/toggle/")
def toggle_feedback_listed(feedback_id: int, db: Session = Depends(get_db), current_admin: User = Depends(ca)):
    admin_service = AdminService(db)
    return admin_service.toggle_feedback_listed(feedback_id)

