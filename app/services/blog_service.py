from sqlalchemy.orm import Session
import boto3
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func
from app.models.user import User
from app.models.blog import Blog
from app.models.feedback import Like, Feedback, View
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


    def get_all_blogs(self, user_id: int):
        blogs = self.db.query(Blog).filter(Blog.is_deleted == False, Blog.is_blocked == False).all()

        # Increment read count if the user has not viewed the blog before
        for blog in blogs:
            existing_view = self.db.query(View).filter(View.blog_id == blog.id, View.user_id == user_id).first()
            if not existing_view:
                blog.read_count += 1
                new_view = View(blog_id=blog.id, user_id=user_id)
                self.db.add(new_view)
                self.db.commit()

        # Fetch feedback and like/unlike counts
        feedback_counts = {row[0]: row[1] for row in self.db.query(Feedback.blog_id, func.count(Feedback.id))
                         .filter(Feedback.is_deleted == False, Feedback.is_listed == True)
                         .group_by(Feedback.blog_id).all()}
        like_counts = {row[0]: row[1] for row in self.db.query(Like.blog_id, func.count(Like.id))
                      .filter(Like.is_like == True)
                      .group_by(Like.blog_id).all()}
        dislike_counts = {row[0]: row[1] for row in self.db.query(Like.blog_id, func.count(Like.id))
                         .filter(Like.is_like == False)
                         .group_by(Like.blog_id).all()}

        return [
            {
                "id": blog.id,
                "title": blog.title,
                "content": blog.content,
                "image_url": blog.image_url,
                "read_count": blog.read_count,
                "feedback_count": feedback_counts.get(blog.id, 0),
                "like_count": like_counts.get(blog.id, 0),
                "dislike_count": dislike_counts.get(blog.id, 0),
                "created_at": blog.created_at,
                "updated_at": blog.updated_at
            }
            for blog in blogs
        ]


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
        blogs = self.db.query(Blog).filter(Blog.author_id == author_id, Blog.is_deleted == False).all()
        return [{"id": blog.id, "title": blog.title, "content": blog.content, "image_url": blog.image_url,
                 "read_count": blog.read_count, "created_at": blog.created_at, "updated_at": blog.updated_at}
                for blog in blogs]


    def edit_blog(self, blog_id: int, author_id: int, title: str = None, content: str = None, image: bytes = None):
        blog = self.db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found or unauthorized")
        if title:
            if self.db.query(Blog).filter(Blog.title == title, Blog.id != blog_id).first():
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


    def delete_blog(self, blog_id: int, author_id: int):
        blog = self.db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found or unauthorized")
        if blog.is_deleted:
            raise HTTPException(status_code=400, detail="Blog is already deleted")
        if blog.image_url:
            image_key = blog.image_url.split(f"{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[-1]
            self.s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=image_key)

        blog.is_deleted = True
        self.db.commit()
        return {"message": "Blog deleted successfully"}


    def like_or_unlike_blog(self, blog_id: int, user_id: int):
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")

        existing_like = self.db.query(Like).filter(Like.blog_id == blog_id, Like.user_id == user_id).first()

        if existing_like:
            if existing_like.is_like:
                self.db.delete(existing_like)  # Unlike (remove the like)
                self.db.commit()
                return {"message": "Blog unliked"}
            else:
                existing_like.is_like = True  # Change dislike to like
                existing_like.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing_like)
                return {"message": "Blog liked"}
        else:
            new_like = Like(blog_id=blog_id, user_id=user_id, is_like=True)
            self.db.add(new_like)
            self.db.commit()
            self.db.refresh(new_like)
            return {"message": "Blog liked successfully"}


    def dislike_or_undislike_blog(self, blog_id: int, user_id: int):
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")

        existing_dislike = self.db.query(Like).filter(Like.blog_id == blog_id, Like.user_id == user_id).first()

        if existing_dislike:
            if existing_dislike.is_like:
                existing_dislike.is_like = False  # Change like to dislike
                existing_dislike.updated_at = datetime.now(timezone.utc)
                self.db.commit()
                self.db.refresh(existing_dislike)
                return {"message": "Blog disliked"}
            else:
                self.db.delete(existing_dislike)  # Dislike (remove the like)
                self.db.commit()
                return {"message": "Blog undisliked"}
        else:
            new_dislike = Like(blog_id=blog_id, user_id=user_id, is_like=False)
            self.db.add(new_dislike)
            self.db.commit()
            self.db.refresh(new_dislike)
            return {"message": "Blog disliked successfully"}


    def get_feedbacks(self, blog_id: int, current_user: User):
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        feedbacks = self.db.query(Feedback).filter(Feedback.blog_id == blog_id, Feedback.is_deleted == False, Feedback.is_listed == True).all()

        return [
            {
                "id": feedback.id,
                "is_current_user_feedback": feedback.user_id == current_user,
                "username": self.db.query(User).filter(User.id == feedback.user_id).first().full_name, 
                "comment": feedback.comment,
                "is_listed": feedback.is_listed, 
                "created_at": feedback.created_at,
                "updated_at": feedback.updated_at
            }
            for feedback in feedbacks
        ]


    def create_feedback(self, blog_id: int, user_id: int, comment: str):
        blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
        if not blog:
            raise HTTPException(status_code=404, detail="Blog not found")
        if not comment.strip():
            raise HTTPException(status_code=400, detail="Comment cannot be empty")
        existing_feedback = self.db.query(Feedback).filter(Feedback.blog_id == blog_id, Feedback.user_id == user_id, Feedback.is_deleted == "False").first()
        if existing_feedback:
            raise HTTPException(status_code=400, detail="User can only provide one feedback per blog")

        new_feedback = Feedback(blog_id=blog_id, user_id=user_id, comment=comment)
        self.db.add(new_feedback)
        self.db.commit()
        self.db.refresh(new_feedback)
        return {"message": "Feedback created successfully", "feedback_id": new_feedback.id}


    def edit_feedback(self, feedback_id: int, user_id: int, comment: str):
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == user_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found or unauthorized")
        if not comment.strip():
            raise HTTPException(status_code=400, detail="Comment cannot be empty")

        feedback.comment = comment
        feedback.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        self.db.refresh(feedback)
        return {"message": "Feedback updated successfully"}


    def delete_feedback(self, feedback_id: int, user_id: int):
        feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == user_id).first()
        if not feedback:
            raise HTTPException(status_code=404, detail="Feedback not found or unauthorized")

        feedback.is_deleted = True
        feedback.updated_at = datetime.now(timezone.utc)
        self.db.commit()
        return {"message": "Feedback deleted successfully"}

