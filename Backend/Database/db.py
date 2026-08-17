from contextlib import contextmanager
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, JSON, DateTime
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = "sqlite:///Database/history.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)

class Base(DeclarativeBase):
    pass

class ChatSession(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True)
    session_id = Column( String, unique=True, nullable=False, index=True)
    messages = Column(JSON, default=list, nullable=False)
    created_at = Column( DateTime, default=datetime.utcnow)
    updated_at = Column( DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

Base.metadata.create_all(engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()