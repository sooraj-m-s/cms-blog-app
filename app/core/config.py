from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

DATABASE_URL = "postgresql://my_user:my_user@localhost:5432/blog_app"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

