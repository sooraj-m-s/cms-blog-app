from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.auth import router
from app.api.blog import router as blog_router
from app.api.admin import router as admin_router
from app.views.user_view import router as user_view_router
from app.views.admin_view import router as admin_view_router
from fastapi.staticfiles import StaticFiles


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")


app.include_router(router, prefix="/api", tags=["auth"])
app.include_router(blog_router, prefix="/api", tags=["blog"])
app.include_router(admin_router, prefix="/api/admin", tags=["admin"])


# Views router for rendering templates

app.include_router(user_view_router, prefix="/user", tags=["auth_views"])
app.include_router(admin_view_router, prefix="/admin", tags=["admin_views"])



