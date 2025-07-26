from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse


router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/login/")
async def get_login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/landing", response_class=HTMLResponse)
async def get_landing_page():
    return templates.TemplateResponse("landing.html", {"request": {}})

