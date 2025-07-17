from sqlalchemy.orm import Session
from app.models.blog import Blog


class BlogService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_blogs(self):
        blogs = self.db.query(Blog).all()
        return [{"id": blog.id, "title": blog.title, "content": blog.content, "image_url": blog.image_url,
                 "read_count": blog.read_count, "created_at": blog.created_at, "updated_at": blog.updated_at}
                for blog in blogs]

