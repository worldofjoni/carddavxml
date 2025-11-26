from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from database import Base

class Contact(Base):
    __tablename__ = "contacts"

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), default="")
    is_primary = Column(Boolean, default=False)
    primary = Column(Integer, default=0)
    frequent = Column(Integer, default=0)
    ringtone = Column(String(255), default="")
    photo_url = Column(String(512), default="")

    # Phone numbers stored as JSON array
    # Format: [{"type": "Mobile", "number": "123456", "accountindex": -1}]
    phones = Column(JSON, default=lambda: [])

    # Email addresses stored as JSON array
    # Format: [{"type": "Home", "email": "test@example.com"}]
    emails = Column(JSON, default=lambda: [])

    # Groups - comma separated group IDs
    groups = Column(String(255), default="")

    # Organization info stored as JSON
    # Format: {"company": "Company", "title": "CEO", "department": ""}
    organization = Column(JSON, default=lambda: {})

    # Address stored as JSON
    # Format: {"street": "", "city": "", "state": "", "postal_code": "", "country": ""}
    address = Column(JSON, default=lambda: {})

    # Website
    website = Column(String(512), default="")

    # Notes
    notes = Column(Text, default="")

    # Birthday (format: YYYY-MM-DD)
    birthday = Column(String(10), default="")

    # CardDAV metadata
    carddav_uid = Column(String(255), default="")
    carddav_etag = Column(String(255), default="")


class ContactGroup(Base):
    __tablename__ = "contact_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    ringtones = Column(String(512), default="")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    carddav_url = Column(String(512), nullable=False)
    carddav_username = Column(String(255), nullable=False)
    carddav_password = Column(String(255), nullable=False)
    sync_enabled = Column(Boolean, default=False)
    bidirectional_sync = Column(Boolean, default=False)  # Push changes back to CardDAV
    auto_sync_interval = Column(Integer, default=3600)  # seconds
    last_sync = Column(String(50), default="")  # ISO format timestamp
    last_sync_status = Column(String(20), default="")  # success, failed, running
    last_sync_message = Column(Text, default="")
