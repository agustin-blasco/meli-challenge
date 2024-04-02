from api.database import Base
from sqlalchemy import Column, String, Integer, Boolean, DateTime
from datetime import datetime, timezone


class IPAddress(Base):
    __tablename__ = "ipaddress"

    id = Column(Integer, primary_key=True, index=True)
    ipaddress = Column(String, unique=True)


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True)
    hashed_password = Column(String)
    role = Column(String)
    active = Column(Boolean)


class AuditLogs(Base):
    __tablename__ = "auditlogs"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String)
    method = Column(String)
    endpoint = Column(String)
    host = Column(String)
    status_code = Column(String)
    timestamp = Column(DateTime, default=datetime.now(timezone.utc))
