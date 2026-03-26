from sqlalchemy import Column, Integer, String, DateTime, Boolean
from pgvector.sqlalchemy import Vector
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

class KeyProfile(Base):
    __tablename__ = "key_profiles"

    id = Column(Integer, primary_key=True)
    key_name = Column(String, unique=True, nullable=False)
    note = Column(String, nullable=False)
    mode = Column(String, nullable=False)
    profile_vector = Column(Vector(12), nullable=False)
