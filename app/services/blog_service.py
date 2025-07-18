from sqlalchemy.orm import Session
import boto3
from datetime import datetime
from fastapi import HTTPException
from app.models.blog import Blog
from app.core.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_BUCKET_NAME


class BlogService:
    def __init__(self, db: Session):
        self.db = db
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )

    def get_all_blogs(self):
        blogs = self.db.query(Blog).all()
        return [{"id": blog.id, "title": blog.title, "content": blog.content, "image_url": blog.image_url,
                 "read_count": blog.read_count, "created_at": blog.created_at, "updated_at": blog.updated_at}
                for blog in blogs]

    def create_blog(self, author_id: int, title: str, content: str, image: bytes = None):
        if self.db.query(Blog).filter(Blog.title == title).first():
            raise HTTPException(status_code=400, detail="Blog title already exists")
        blog = Blog(author_id=author_id, title=title, content=content)
        if image:
            # Upload image to S3
            image_key = f"blogs/{author_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            self.s3.put_object(Bucket=AWS_BUCKET_NAME, Key=image_key, Body=image, ContentType='image/jpeg')
            blog.image_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{image_key}"
        self.db.add(blog)
        self.db.commit()
        self.db.refresh(blog)
        return {"message": "Blog created successfully", "blog_id": blog.id}

    def get_user_blogs(self, author_id: int):
        blogs = self.db.query(Blog).filter(Blog.author_id == author_id).all()
        return [{"id": blog.id, "title": blog.title, "content": blog.content, "image_url": blog.image_url,
                 "read_count": blog.read_count, "created_at": blog.created_at, "updated_at": blog.updated_at}
                for blog in blogs]

    def edit_blog(self, blog_id: int, author_id: int, title: str = None, content: str = None, image: bytes = None):
        blog = self.db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found or unauthorized")
        if title:
            if self.db.query(Blog).filter(Blog.title == title).first():
                raise HTTPException(status_code=400, detail="Blog title already exists")
            blog.title = title
        if content:
            blog.content = content
        if image:
            if blog.image_url:
                # Delete old image from S3
                image_key = blog.image_url.split(f"{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[-1]
                self.s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=image_key)
            image_key = f"blogs/{author_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            self.s3.put_object(Bucket=AWS_BUCKET_NAME, Key=image_key, Body=image, ContentType='image/jpeg')
            blog.image_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{image_key}"
        self.db.commit()
        self.db.refresh(blog)
        return {"message": "Blog updated successfully"}

