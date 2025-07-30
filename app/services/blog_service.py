from sqlalchemy.orm import Session
import boto3, logging, io, re
from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import func, case
from sqlalchemy.exc import SQLAlchemyError
from PIL import Image, UnidentifiedImageError
from app.models.user import User
from app.models.blog import Blog
from app.models.feedback import Like, Feedback, View
from app.core.config import AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, AWS_REGION, AWS_BUCKET_NAME


logger = logging.getLogger(__name__)

class BlogService:
    def __init__(self, db: Session):
        self.db = db
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_ACCESS_KEY_ID,
            aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
            region_name=AWS_REGION
        )


    def get_all_blogs(self, page: int = 1, page_size: int = 10):
        try:
            offset = (page - 1) * page_size
            blogs_with_counts = (
                self.db.query(
                    Blog.id,
                    Blog.title,
                    Blog.content,
                    Blog.image_url,
                    Blog.read_count,
                    Blog.created_at,
                    func.sum(case((Like.is_like == True, 1), else_=0)).label("like_count"),
                    func.sum(case((Like.is_like == False, 1), else_=0)).label("dislike_count")
                )
                .outerjoin(Like, Blog.id == Like.blog_id)
                .filter(Blog.is_deleted == False, Blog.is_blocked == False)
                .group_by(Blog.id)
                .order_by(Blog.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return {
                "page": page,
                "page_size": page_size,
                "blogs": [
                    {
                        "id": blog.id,
                        "title": blog.title,
                        "content": blog.content,
                        "image_url": blog.image_url,
                        "read_count": blog.read_count,
                        "like_count": blog.like_count or 0,
                        "dislike_count": blog.dislike_count or 0,
                        "created_at": blog.created_at,
                    }
                    for blog in blogs_with_counts
                ]
            }
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error while fetching blogs: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error while fetching blogs: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")
    

    def view_blog_detail(self, blog_id: int, current_user_id: int):
        try:
            result = (
                self.db.query(
                    Blog,
                    func.count(case((Like.is_like == True, Like.id), else_=0)).label("like_count"),
                    func.count(case((Like.is_like == False, Like.id), else_=0)).label("dislike_count"),
                )
                .outerjoin(Feedback, Blog.id == Feedback.blog_id)
                .outerjoin(Like, Blog.id == Like.blog_id)
                .filter(Blog.id == blog_id, Blog.is_deleted == False, Blog.is_blocked == False)
                .group_by(Blog.id)
                .first()
            )
            if not result:
                raise HTTPException(status_code=404, detail="Blog not found")
            blog = result[0]

            existing_view = self.db.query(View).filter(View.blog_id == blog_id, View.user_id == current_user_id).first()
            if not existing_view:
                new_view = View(blog_id=blog_id, user_id=current_user_id)
                self.db.add(new_view)
                blog.read_count += 1
                self.db.commit()

            return {
                "id": blog.id,
                "title": blog.title,
                "content": blog.content,
                "image_url": blog.image_url,
                "read_count": blog.read_count,
                "like_count": result.like_count,
                "dislike_count": result.dislike_count,
                "created_at": blog.created_at,
                "updated_at": blog.updated_at,
            }
        except HTTPException as e:
            logger.warning(f"HTTP error while fetching blog: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in view_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in view_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def create_blog(self, author_id: int, title: str, content: str, image: bytes = None):
        try:
            if not re.match(r'^[A-Za-z ]+$', title) or len(title.strip()) < 4:
                raise HTTPException(status_code=400, detail="Title must be at least 4 characters and contain only letters and spaces")
            if not content.strip():
                raise HTTPException(status_code=400, detail="Content must not be empty")
            if self.db.query(Blog).filter(Blog.title == title).first():
                raise HTTPException(status_code=400, detail="Blog title already exists")
            
            blog = Blog(author_id=author_id, title=title, content=content)
            if image:
                if len(image) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="Image too large")
                try:
                    img = Image.open(io.BytesIO(image))
                    img.verify()
                    format = img.format.lower()
                    mime_type = f'image/{format}'
                except UnidentifiedImageError:
                    raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

                # Upload to S3
                image_key = f"blogs/{author_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                self.s3.put_object(
                    Bucket=AWS_BUCKET_NAME,
                    Key=image_key,
                    Body=image,
                    ContentType=mime_type
                )
                blog.image_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{image_key}"
            self.db.add(blog)
            self.db.commit()
            self.db.refresh(blog)

            return {"message": "Blog created successfully", "blog_id": blog.id}
        except HTTPException as e:
            logger.warning(f"HTTP error while creating blog: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error while creating blog: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error while creating blog: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def get_user_blogs(self, author_id: int, page: int = 1, page_size: int = 10):
        try:
            offset = (page - 1) * page_size

            blogs = (
                self.db.query(Blog)
                .filter(Blog.author_id == author_id, Blog.is_deleted == False)
                .order_by(Blog.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return {
                "page": page,
                "page_size": page_size,
                "blogs": [
                    {
                        "id": blog.id,
                        "title": blog.title,
                        "content": blog.content,
                        "image_url": blog.image_url,
                        "read_count": blog.read_count,
                        "created_at": blog.created_at,
                        "updated_at": blog.updated_at,
                    }
                    for blog in blogs
                ]
            }
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_user_blogs: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in get_user_blogs: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def edit_blog(self, blog_id: int, author_id: int, title: str = None, content: str = None, image: bytes = None):
        try:
            blog = self.db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author_id).first()
            if not blog:
                raise HTTPException(status_code=404, detail="Blog not found or unauthorized")
            if title:
                if not re.match(r'^[A-Za-z ]+$', title) or len(title.strip()) < 4:
                    raise HTTPException(status_code=400, detail="Title must be at least 4 characters and contain only letters and spaces")
                if self.db.query(Blog).filter(Blog.title == title, Blog.id != blog_id).first():
                    raise HTTPException(status_code=400, detail="Blog title already exists")
                blog.title = title
            if content:
                if not content.strip():
                    raise HTTPException(status_code=400, detail="Content must not be empty")
                blog.content = content
            if image:
                if len(image) > 5 * 1024 * 1024:
                    raise HTTPException(status_code=400, detail="Image too large")
                if blog.image_url:
                    # Delete old image from S3
                    try:
                        image_key = blog.image_url.split(f"{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[-1]
                        self.s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=image_key)
                    except Exception as s3_error:
                        logger.error(f"Error deleting old image from S3: {s3_error}")
                    
                try:
                    img = Image.open(io.BytesIO(image))
                    img.verify()
                    format = img.format.lower()
                    mime_type = f'image/{format}'
                except UnidentifiedImageError:
                    raise HTTPException(status_code=400, detail="Uploaded file is not a valid image")

                # Upload to S3
                image_key = f"blogs/{author_id}/{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"
                self.s3.put_object(
                    Bucket=AWS_BUCKET_NAME,
                    Key=image_key,
                    Body=image,
                    ContentType=mime_type
                )
                blog.image_url = f"https://{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{image_key}"
            self.db.commit()
            self.db.refresh(blog)

            return {"message": "Blog updated successfully"}
        except HTTPException as e:
            logger.warning(f"Validation error in edit_blog: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in edit_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in edit_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def delete_blog(self, blog_id: int, author_id: int):
        try:
            blog = self.db.query(Blog).filter(Blog.id == blog_id, Blog.author_id == author_id).first()
            if not blog:
                raise HTTPException(status_code=404, detail="Blog not found or unauthorized")
            if blog.is_deleted:
                raise HTTPException(status_code=400, detail="Blog is already deleted")
            
            if blog.image_url:
                try:
                    image_key = blog.image_url.split(f"{AWS_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/")[-1]
                    self.s3.delete_object(Bucket=AWS_BUCKET_NAME, Key=image_key)
                except Exception as s3_error:
                    logger.error(f"Error deleting image from S3: {s3_error}")

            blog.is_deleted = True
            self.db.commit()

            return {"message": "Blog deleted successfully"}
        except HTTPException as e:
            logger.warning(f"Validation error in delete_blog: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in delete_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def like_or_unlike_blog(self, blog_id: int, user_id: int):
        try:
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
        except HTTPException as e:
            logger.warning(f"Validation error in like_or_unlike_blog: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in like_or_unlike_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in like_or_unlike_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def dislike_or_undislike_blog(self, blog_id: int, user_id: int):
        try:
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
        except HTTPException as e:
            logger.warning(f"Validation error in dislike_or_undislike_blog: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in dislike_or_undislike_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in dislike_or_undislike_blog: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def get_feedbacks(self, blog_id: int, current_user: User, page: int = 1, page_size: int = 10):
        try:
            blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
            if not blog:
                raise HTTPException(status_code=404, detail="Blog not found")
            offset = (page - 1) * page_size

            feedbacks = (
                self.db.query(Feedback)
                .filter(
                    Feedback.blog_id == blog_id,
                    Feedback.is_deleted == False,
                    Feedback.is_listed == True
                )
                .order_by(Feedback.created_at.desc())
                .offset(offset)
                .limit(page_size)
                .all()
            )

            return {
                "page": page,
                "page_size": page_size,
                "blogs": [
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
            }
        except HTTPException as e:
            logger.warning(f"Validation error in get_feedbacks: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in get_feedbacks: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in get_feedbacks: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def create_feedback(self, blog_id: int, user_id: int, comment: str):
        try:
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
        except HTTPException as e:
            logger.warning(f"Validation error in create_feedback: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in create_feedback: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in create_feedback: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def edit_feedback(self, feedback_id: int, user_id: int, comment: str):
        try:
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
        except HTTPException as e:
            logger.warning(f"Validation error in edit_feedback: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in edit_feedback: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in edit_feedback: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")


    def delete_feedback(self, feedback_id: int, user_id: int):
        try:
            feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id, Feedback.user_id == user_id).first()
            if not feedback:
                raise HTTPException(status_code=404, detail="Feedback not found or unauthorized")

            feedback.is_deleted = True
            feedback.updated_at = datetime.now(timezone.utc)
            self.db.commit()

            return {"message": "Feedback deleted successfully"}
        except HTTPException as e:
            logger.warning(f"Validation error in delete_feedback: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error in delete_feedback: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error in delete_feedback: {e}")
            self.db.rollback()
            raise HTTPException(status_code=500, detail="Internal server error")

