from datetime import datetime, timedelta, timezone
from fastapi import HTTPException
import jwt, logging
from fastapi.responses import JSONResponse
from app.models.user import User
from app.models.blog import Blog
from app.models.feedback import Feedback
from app.core.config import SECRET_KEY
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError


logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
access_token_expires = timedelta(minutes=15)
refresh_token_expires = timedelta(days=30)

class AdminService:
    def __init__(self, db: Session):
        self.db = db


    def admin_login_user(self, email: str, password: str):
        try:
            db_user = self.db.query(User).filter(User.email == email).first()
            if not db_user or not pwd_context.verify(password, db_user.password):
                raise HTTPException(status_code=401, detail="Invalid credentials")
            if not db_user.is_admin:
                raise HTTPException(status_code=403, detail="Admin access required")

            # Generate token
            access_token = jwt.encode(
                {"sub": db_user.email, "id": db_user.id, "exp": datetime.now(timezone.utc) + access_token_expires},
                SECRET_KEY,
                algorithm="HS256"
            )
            refresh_token = jwt.encode(
                {"sub": db_user.email, "id": db_user.id, "type": "refresh", "exp": datetime.now(timezone.utc) + refresh_token_expires},
                SECRET_KEY,
                algorithm="HS256"
            )

            response = JSONResponse(content={"message": "Login successful"})
            response.set_cookie(key="access_token", value=access_token, httponly=True, max_age=access_token_expires, secure=False, samesite="lax")
            response.set_cookie(key="refresh_token", value=refresh_token, httponly=True, max_age=refresh_token_expires, secure=False, samesite="lax")
            
            return response
        except HTTPException as e:
            logger.warning(f"Admin login failed for {email}: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error during admin login for {email}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error during admin login for {email}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def admin_get_all_blogs(self, page: int = 1, page_size: int = 10):
        try:
            offset = (page - 1) * page_size
            blogs = self.db.query(Blog).filter(Blog.is_deleted == False).offset(offset).limit(page_size).all()
            total_blogs = self.db.query(Blog).filter(Blog.is_deleted == False).count()

            if not blogs:
                raise HTTPException(status_code=404, detail="No blogs found")
            
            return {
                "blogs": [
                    {
                        "id": blog.id,
                        "title": blog.title,
                        "content": blog.content,
                        "image_url": blog.image_url,
                        "is_blocked": blog.is_blocked,
                        "created_at": blog.created_at,
                        "updated_at": blog.updated_at
                    } for blog in blogs
                ],
                "total_blogs": total_blogs,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_blogs + page_size - 1) // page_size
            }
        except HTTPException as e:
            logger.warning(f"Error fetching blogs: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching blogs: {e}")
            raise HTTPException(status_code=500, detail=f"Database error occurred: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error while fetching blogs: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def list_all_users(self, page: int = 1, page_size: int = 10):
        try:
            offset = (page - 1) * page_size
            users = self.db.query(User).filter(User.is_admin == False).offset(offset).limit(page_size).all()
            total_users = self.db.query(User).filter(User.is_admin == False).count()

            if not users:
                raise HTTPException(status_code=404, detail="No users found")
            
            return {
                "users": [
                    {
                        "id": user.id,
                        "name": user.full_name,
                        "email": user.email,
                        "is_blocked": user.is_blocked,
                        "created_at": user.created_at
                    } for user in users
                ],
                "total_users": total_users,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_users + page_size - 1) // page_size
            }
        except HTTPException as e:
            logger.warning(f"Error listing users: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching users: {e}")
            raise HTTPException(status_code=500, detail=f"Database error occurred: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error while fetching users: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def block_unblock_user(self, user_id: int):
        try:
            user = self.db.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            user.is_blocked = not user.is_blocked
            self.db.commit()
            self.db.refresh(user)
            
            return {"message": f"User is_blocked toggled to {user.is_blocked}", "user_id": user.id}
        except HTTPException as e:
            logger.warning(f"Error toggling block status for user ID {user_id}: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error while toggling block status for user ID {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error while toggling block status for user ID {user_id}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def block_unblock_blog(self, blog_id: int):
        try:
            blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
            if not blog:
                raise HTTPException(status_code=404, detail="Blog not found")
            if blog.is_deleted:
                raise HTTPException(status_code=400, detail="Blog is deleted and cannot be blocked")

            blog.is_blocked = not blog.is_blocked
            self.db.commit()
            self.db.refresh(blog)

            return {"message": f"Blog is_blocked toggled to {blog.is_blocked}", "blog_id": blog.id}
        except HTTPException as e:
            logger.warning(f"Error toggling block status for blog ID {blog_id}: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error while toggling block status for blog ID {blog_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error while blocking/unblocking blog ID {blog_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def get_feedbacks(self, blog_id: int, page: int = 1, page_size: int = 10):
        try:
            blog = self.db.query(Blog).filter(Blog.id == blog_id).first()
            if not blog:
                raise HTTPException(status_code=404, detail="Blog not found")

            offset = (page - 1) * page_size
            feedbacks = self.db.query(Feedback).filter(Feedback.blog_id == blog_id, Feedback.is_deleted == False).offset(offset).limit(page_size).all()
            total_feedbacks = self.db.query(Feedback).filter(Feedback.blog_id == blog_id, Feedback.is_deleted == False).count()

            if not feedbacks:
                raise HTTPException(status_code=404, detail="No feedbacks found for this blog")

            return {
                "feedbacks": [
                    {
                        "id": feedback.id,
                        "user_id": feedback.user_id,
                        "content": feedback.comment,
                        "is_listed": feedback.is_listed,
                        "created_at": feedback.created_at
                    } for feedback in feedbacks
                ],
                "total_feedbacks": total_feedbacks,
                "page": page,
                "page_size": page_size,
                "total_pages": (total_feedbacks + page_size - 1) // page_size
            }
        except HTTPException as e:
            logger.warning(f"Error fetching feedbacks for blog ID {blog_id}: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            logger.error(f"Database error while fetching feedbacks for blog ID {blog_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            logger.exception(f"Unexpected error while fetching feedbacks for blog ID {blog_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")


    def toggle_feedback_listed(self, feedback_id: int):
        try:
            feedback = self.db.query(Feedback).filter(Feedback.id == feedback_id).first()
            if not feedback:
                raise HTTPException(status_code=404, detail="Feedback not found")
            if feedback.is_deleted:
                raise HTTPException(status_code=400, detail="Feedback is deleted and cannot be toggled")

            feedback.is_listed = not feedback.is_listed
            self.db.commit()
            self.db.refresh(feedback)

            return {"message": f"Feedback is_listed toggled to {feedback.is_listed}", "feedback_id": feedback.id}
        except HTTPException as e:
            logger.warning(f"Error toggling feedback listed status for ID {feedback_id}: {e.detail}")
            raise e
        except SQLAlchemyError as e:
            self.db.rollback()
            logger.error(f"Database error while toggling feedback listed status for ID {feedback_id}: {e}")
            raise HTTPException(status_code=500, detail="Database error occurred")
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error while toggling feedback listed status for ID {feedback_id}: {e}")
            raise HTTPException(status_code=500, detail="Internal server error")

