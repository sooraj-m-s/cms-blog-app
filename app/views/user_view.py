from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from app.core.config import BASE_URL


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login/")
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "base_url": BASE_URL})


@router.get("/landing")
async def get_landing_page(request: Request):
    return templates.TemplateResponse("landing.html", {"request": {request}, "base_url": BASE_URL})

