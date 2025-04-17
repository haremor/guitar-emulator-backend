from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base
from utils.config import settings

engine = create_engine(f'postgresql+psycopg://{settings.db_url}')

# Create a session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()