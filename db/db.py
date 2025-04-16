from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db.models import Base

engine = create_engine('postgresql+psycopg://postgres:6565@localhost/G')
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()