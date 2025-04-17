from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import MainBase, FileBase
from utils.config import settings

main_engine = create_engine(f'postgresql+psycopg://{settings.main_db_url}')
file_db_engine = create_engine(f'postgresql+psycopg://{settings.file_db_url}')

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=main_engine)
FileSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=file_db_engine)

MainBase.metadata.create_all(bind=main_engine)
FileBase.metadata.create_all(bind=file_db_engine)

async def get_main_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_file_db():
    db = FileSessionLocal()
    try:
        yield db
    finally:
        db.close()