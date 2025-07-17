from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.config import get_db
from app.services.blog_service import BlogService


router = APIRouter()

@router.get("/landing/")
def get_landing_page(db: Session = Depends(get_db)):
    blog_service = BlogService(db)
    return {"blogs": blog_service.get_all_blogs()}

