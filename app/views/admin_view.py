from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.core.config import BASE_URL


router = APIRouter()
templates = Jinja2Templates(directory="app/templates/admin")

@router.get("/login/")
async def get_admin_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "base_url": BASE_URL})


@router.get("/dashboard/")
async def get_admin_dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request, "base_url": BASE_URL})

