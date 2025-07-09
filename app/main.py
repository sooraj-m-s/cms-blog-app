from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from .core.config import get_db
from .models.user import User
from sqlalchemy.sql import text
from datetime import datetime
from fastapi import Depends


app = FastAPI()
templates = Jinja2Templates(directory="app/templates")

@app.post("/register")
async def register_user(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db.execute(text("INSERT INTO users (username, email, password, created_at) VALUES (:username, :email, :password, :created_at)"),
               {"username": username, "email": email, "password": password, "created_at": datetime.now()})
    db.commit()
    return templates.TemplateResponse("layout/register_success.html", {"request": request, "username": username})

@app.get("/register", response_class=HTMLResponse)
async def register_form(request: Request):
    return templates.TemplateResponse("layout/register.html", {"request": request})

