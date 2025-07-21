from fastapi import FastAPI
from app.api.auth import router
from app.api.blog import router as blog_router
from app.api.admin import router as admin_router
from app.views.html_view import router as html_view_router
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(router, tags=["auth"])
app.include_router(blog_router, tags=["blog"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])


# Views router for rendering templates

app.include_router(html_view_router, tags=["auth_views"])

