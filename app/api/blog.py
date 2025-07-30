from fastapi import APIRouter, Depends, UploadFile, Form, File
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.services.blog_service import BlogService
from app.models.user import User
from app.dependencies import get_current_user as cu
from app.schemas.blog_schema import FeedbackCreate


router = APIRouter()

@router.get("/landing/")
def get_landing_page(page: int = 1, page_size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return {"blogs": blog_service.get_all_blogs(page, page_size)}


@router.get("/blog/{blog_id}/view/")
def view_blog_detail(blog_id: int, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return {"blog": blog_service.view_blog_detail(blog_id, current_user.id)}


@router.post("/blogs/")
async def create_blog(title: str = Form(...), content: str = Form(...), image: UploadFile = File(None), db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    image_data = await image.read() if image else None
    return blog_service.create_blog(current_user.id, title, content, image_data)


@router.get("/blogs/")
def list_user_blogs(page: int = 1, page_size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return {"blogs": blog_service.get_user_blogs(current_user.id, page, page_size)}


@router.patch("/blogs/{blog_id}")
async def edit_blog(blog_id: int, title: str = Form(None), content: str = Form(None), image: UploadFile = File(None), db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    image_data = await image.read() if image else None
    return blog_service.edit_blog(blog_id, current_user.id, title, content, image_data)


@router.delete("/blogs/{blog_id}/delete/")
def delete_blog(blog_id: int, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.delete_blog(blog_id, current_user.id)


@router.patch("/blogs/{blog_id}/like")
def like_or_unlike_blog(blog_id: int, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.like_or_unlike_blog(blog_id, current_user.id)


@router.patch("/blogs/{blog_id}/dislike")
def dislike_or_undislike_blog(blog_id: int, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.dislike_or_undislike_blog(blog_id, current_user.id)


@router.get("/blogs/{blog_id}/feedbacks")
def get_feedbacks(blog_id: int, page: int = 1, page_size: int = 10, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.get_feedbacks(blog_id, current_user.id, page, page_size)


@router.post("/blogs/{blog_id}/feedback")
def create_feedback(blog_id: int, feedback: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.create_feedback(blog_id, current_user.id, feedback.comment)


@router.patch("/blogs/feedback/{feedback_id}")
def edit_feedback(feedback_id: int, feedback: FeedbackCreate, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.edit_feedback(feedback_id, current_user.id, feedback.comment)


@router.delete("/blogs/feedback/{feedback_id}/delete/")
def delete_feedback(feedback_id: int, db: Session = Depends(get_db), current_user: User = Depends(cu)):
    blog_service = BlogService(db)
    return blog_service.delete_feedback(feedback_id, current_user.id)

