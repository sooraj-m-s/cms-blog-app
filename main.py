from fastapi import FastAPI
from app.api.auth import router
from app.api.blog import router as blog_router
from app.api.admin import router as admin_router


app = FastAPI()

app.include_router(router, tags=["auth"])
app.include_router(blog_router, tags=["blog"])
app.include_router(admin_router, prefix="/admin", tags=["admin"])

