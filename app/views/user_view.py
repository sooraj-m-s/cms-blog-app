from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import jwt
from app.models.logout import Logout
from app.core.config import BASE_URL
from app.db.database import get_db


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login/")
def get_login_page(request: Request,  db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    
    if token:
        try:
            revoked_token = db.query(Logout).filter(Logout.token == token).first()
            if not revoked_token:
                return RedirectResponse(url=f"{BASE_URL}/user/landing/")
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass
    
    return templates.TemplateResponse("login.html", {"request": request, "base_url": BASE_URL})


@router.get("/landing/")
async def get_landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": request, "base_url": BASE_URL})


@router.get("/blog-detail/")
def get_blog_detail(request: Request):
    return templates.TemplateResponse("blog.html", {"request": request, "base_url": BASE_URL})


@router.get("/my-blog/")
def get_my_blog(request: Request):
    return templates.TemplateResponse("my_blog.html", {"request": request, "base_url": BASE_URL})

