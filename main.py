from fastapi import FastAPI
from app.api.auth import router
from app.api.blog import router as blog_router


app = FastAPI()

app.include_router(router, tags=["auth"])
app.include_router(blog_router, tags=["blog"])

