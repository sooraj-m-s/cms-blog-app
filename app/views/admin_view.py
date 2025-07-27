from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from app.core.config import BASE_URL
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import jwt
from app.models.logout import Logout
from app.db.database import get_db


router = APIRouter()
templates = Jinja2Templates(directory="app/templates/admin")

@router.get("/login/")
async def get_admin_login_page(request: Request,   db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    
    if token:
        try:
            revoked_token = db.query(Logout).filter(Logout.token == token).first()
            if not revoked_token:
                return RedirectResponse(url=f"{BASE_URL}/admin/dashboard/")
        except jwt.ExpiredSignatureError:
            pass
        except jwt.InvalidTokenError:
            pass
    return templates.TemplateResponse("login.html", {"request": request, "base_url": BASE_URL})


@router.get("/dashboard/")
async def get_admin_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "base_url": BASE_URL})

