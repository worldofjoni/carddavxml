from pydantic import BaseModel, Field
from typing import List, Dict, Optional

# Phone number schema
class PhoneNumber(BaseModel):
    type: str = "Mobile"
    number: str
    accountindex: int = -1

# Email schema
class Email(BaseModel):
    type: str = "Home"
    email: str

# Organization schema
class Organization(BaseModel):
    company: str = ""
    title: str = ""
    department: str = ""

# Address schema
class Address(BaseModel):
    street: str = ""
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = ""

# Contact schemas
class ContactBase(BaseModel):
    first_name: str
    last_name: str = ""
    is_primary: bool = False
    primary: int = 0
    frequent: int = 0
    ringtone: str = ""
    photo_url: str = ""
    phones: List[Dict] = Field(default_factory=list)
    emails: List[Dict] = Field(default_factory=list)
    groups: str = ""
    organization: Dict = Field(default_factory=dict)
    address: Dict = Field(default_factory=dict)
    website: str = ""
    notes: str = ""
    birthday: str = ""

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    is_primary: Optional[bool] = None
    primary: Optional[int] = None
    frequent: Optional[int] = None
    ringtone: Optional[str] = None
    photo_url: Optional[str] = None
    phones: Optional[List[Dict]] = None
    emails: Optional[List[Dict]] = None
    groups: Optional[str] = None
    organization: Optional[Dict] = None
    address: Optional[Dict] = None
    website: Optional[str] = None
    notes: Optional[str] = None
    birthday: Optional[str] = None

class ContactResponse(ContactBase):
    id: int
    carddav_uid: str = ""
    carddav_etag: str = ""

    class Config:
        from_attributes = True

# Contact Group schemas
class ContactGroupBase(BaseModel):
    name: str
    ringtones: str = ""

class ContactGroupCreate(ContactGroupBase):
    pass

class ContactGroupResponse(ContactGroupBase):
    id: int

    class Config:
        from_attributes = True

# Settings schemas
class SettingsBase(BaseModel):
    carddav_url: str
    carddav_username: str
    carddav_password: str
    sync_enabled: bool = False
    auto_sync_interval: int = 3600

class SettingsCreate(SettingsBase):
    pass

class SettingsResponse(SettingsBase):
    id: int

    class Config:
        from_attributes = True

# CardDAV sync schema
class CardDAVSync(BaseModel):
    carddav_url: str
    carddav_username: str
    carddav_password: str
    clear_existing: bool = False
