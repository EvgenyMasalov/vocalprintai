from sqlalchemy import Column, Integer, String, DateTime, Boolean
from datetime import datetime
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_admin = Column(Boolean, default=False)
    balance = Column(Integer, default=0)
    login_count = Column(Integer, default=0)
    request_count = Column(Integer, default=0)
    spectral_count = Column(Integer, default=0)
    deep_research_count = Column(Integer, default=0)
    replenishment_total = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
