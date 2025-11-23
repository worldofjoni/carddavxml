from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy.orm import Session
from typing import List
import logging
import atexit

from database import engine, Base, get_db
from models import Contact, ContactGroup, Settings
from schemas import (
    ContactCreate, ContactUpdate, ContactResponse,
    ContactGroupCreate, ContactGroupResponse,
    SettingsCreate, SettingsResponse,
    CardDAVSync, CardDAVDebug
)
from xml_generator import generate_grandstream_xml
from carddav_client import CardDAVClient
from sync_scheduler import start_scheduler, stop_scheduler, update_scheduler

# Create database tables
Base.metadata.create_all(bind=engine)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="CardDAV to XML Phonebook", version="1.0.0")

# Start background scheduler
@app.on_event("startup")
async def startup_event():
    logger.info("Starting application...")
    start_scheduler()

# Stop scheduler on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down application...")
    stop_scheduler()

# Also register cleanup handler
atexit.register(stop_scheduler)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    return {"message": "CardDAV to XML Phonebook API", "status": "running"}

# Contact endpoints
@app.get("/api/contacts", response_model=List[ContactResponse])
async def get_contacts(db: Session = Depends(get_db)):
    """Get all contacts"""
    contacts = db.query(Contact).all()
    return contacts

@app.get("/api/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: int, db: Session = Depends(get_db)):
    """Get a specific contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    return contact

@app.post("/api/contacts", response_model=ContactResponse)
async def create_contact(contact: ContactCreate, db: Session = Depends(get_db)):
    """Create a new contact"""
    db_contact = Contact(**contact.model_dump())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.put("/api/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(
    contact_id: int,
    contact: ContactUpdate,
    db: Session = Depends(get_db)
):
    """Update a contact"""
    db_contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not db_contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    for key, value in contact.model_dump(exclude_unset=True).items():
        setattr(db_contact, key, value)

    db.commit()
    db.refresh(db_contact)
    return db_contact

@app.delete("/api/contacts/{contact_id}")
async def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    """Delete a contact"""
    contact = db.query(Contact).filter(Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")

    db.delete(contact)
    db.commit()
    return {"message": "Contact deleted successfully"}

# Contact Groups endpoints
@app.get("/api/groups", response_model=List[ContactGroupResponse])
async def get_groups(db: Session = Depends(get_db)):
    """Get all contact groups"""
    groups = db.query(ContactGroup).all()
    return groups

@app.post("/api/groups", response_model=ContactGroupResponse)
async def create_group(group: ContactGroupCreate, db: Session = Depends(get_db)):
    """Create a new contact group"""
    db_group = ContactGroup(**group.model_dump())
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    return db_group

@app.delete("/api/groups/{group_id}")
async def delete_group(group_id: int, db: Session = Depends(get_db)):
    """Delete a contact group"""
    group = db.query(ContactGroup).filter(ContactGroup.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")

    db.delete(group)
    db.commit()
    return {"message": "Group deleted successfully"}

# Settings endpoints
@app.get("/api/settings", response_model=SettingsResponse)
async def get_settings(db: Session = Depends(get_db)):
    """Get CardDAV settings"""
    settings = db.query(Settings).first()
    if not settings:
        # Create default settings
        settings = Settings(
            carddav_url="",
            carddav_username="",
            carddav_password="",
            sync_enabled=False
        )
        db.add(settings)
        db.commit()
        db.refresh(settings)
    return settings

@app.put("/api/settings", response_model=SettingsResponse)
async def update_settings(settings: SettingsCreate, db: Session = Depends(get_db)):
    """Update CardDAV settings"""
    db_settings = db.query(Settings).first()

    if not db_settings:
        db_settings = Settings(**settings.model_dump())
        db.add(db_settings)
    else:
        for key, value in settings.model_dump().items():
            setattr(db_settings, key, value)

    db.commit()
    db.refresh(db_settings)

    # Update the background sync scheduler
    update_scheduler()
    logger.info("Settings updated, scheduler reconfigured")

    return db_settings

# CardDAV sync endpoint
@app.post("/api/sync/carddav")
async def sync_carddav(sync_data: CardDAVSync, db: Session = Depends(get_db)):
    """Sync contacts from CardDAV server"""
    try:
        client = CardDAVClient(
            url=sync_data.carddav_url,
            username=sync_data.carddav_username,
            password=sync_data.carddav_password,
            verify_ssl=sync_data.verify_ssl
        )

        contacts = client.fetch_contacts()

        # Clear existing contacts if requested
        if sync_data.clear_existing:
            db.query(Contact).delete()

        # Import contacts
        imported_count = 0
        for contact_data in contacts:
            db_contact = Contact(**contact_data)
            db.add(db_contact)
            imported_count += 1

        db.commit()

        return {
            "message": f"Successfully imported {imported_count} contacts",
            "count": imported_count
        }
    except Exception as e:
        logger.error(f"CardDAV sync error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"CardDAV sync failed: {str(e)}")

@app.post("/api/sync/test")
async def test_carddav_connection(sync_data: CardDAVSync):
    """Test CardDAV connection"""
    try:
        client = CardDAVClient(
            url=sync_data.carddav_url,
            username=sync_data.carddav_username,
            password=sync_data.carddav_password,
            verify_ssl=sync_data.verify_ssl
        )

        # Try to connect
        client.connect()

        return {"message": "Connection successful", "status": "ok"}
    except Exception as e:
        logger.error(f"CardDAV connection test error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Connection failed: {str(e)}")

@app.post("/api/sync/debug")
async def debug_carddav_connection(debug_data: CardDAVDebug):
    """Debug CardDAV connection with detailed diagnostics"""
    import requests
    from requests.auth import HTTPBasicAuth

    results = {
        "url": debug_data.carddav_url,
        "username": debug_data.carddav_username,
        "verify_ssl": debug_data.verify_ssl,
        "tests": []
    }

    # Test 1: Basic HTTP connectivity
    try:
        response = requests.get(
            debug_data.carddav_url,
            auth=HTTPBasicAuth(debug_data.carddav_username, debug_data.carddav_password),
            timeout=10,
            verify=debug_data.verify_ssl
        )
        results["tests"].append({
            "name": "HTTP Connectivity",
            "status": "success",
            "details": {
                "status_code": response.status_code,
                "server": response.headers.get('Server', 'Unknown'),
                "dav_header": response.headers.get('DAV', 'Not present')
            }
        })
    except Exception as e:
        results["tests"].append({
            "name": "HTTP Connectivity",
            "status": "failed",
            "error": str(e)
        })

    # Test 2: DAV OPTIONS
    try:
        response = requests.request(
            'OPTIONS',
            debug_data.carddav_url,
            auth=HTTPBasicAuth(debug_data.carddav_username, debug_data.carddav_password),
            timeout=10,
            verify=debug_data.verify_ssl
        )
        results["tests"].append({
            "name": "DAV OPTIONS",
            "status": "success",
            "details": {
                "status_code": response.status_code,
                "allow": response.headers.get('Allow', 'Not present'),
                "dav": response.headers.get('DAV', 'Not present')
            }
        })
    except Exception as e:
        results["tests"].append({
            "name": "DAV OPTIONS",
            "status": "failed",
            "error": str(e)
        })

    # Test 3: caldav client connection
    try:
        client = CardDAVClient(
            url=debug_data.carddav_url,
            username=debug_data.carddav_username,
            password=debug_data.carddav_password,
            verify_ssl=debug_data.verify_ssl
        )
        client.connect()
        results["tests"].append({
            "name": "CardDAV Client Connection",
            "status": "success",
            "details": "Successfully connected to CardDAV server"
        })
    except Exception as e:
        results["tests"].append({
            "name": "CardDAV Client Connection",
            "status": "failed",
            "error": str(e)
        })

    # Test 4: Fetch contacts count
    try:
        client = CardDAVClient(
            url=debug_data.carddav_url,
            username=debug_data.carddav_username,
            password=debug_data.carddav_password,
            verify_ssl=debug_data.verify_ssl
        )
        contacts = client.fetch_contacts()
        results["tests"].append({
            "name": "Fetch Contacts",
            "status": "success",
            "details": f"Found {len(contacts)} contacts"
        })
    except Exception as e:
        results["tests"].append({
            "name": "Fetch Contacts",
            "status": "failed",
            "error": str(e)
        })

    # Generate suggestions
    from urllib.parse import urlparse
    parsed = urlparse(debug_data.carddav_url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    results["suggestions"] = [
        f"{base_url}/remote.php/dav/addressbooks/users/{debug_data.carddav_username}/",
        f"{base_url}/remote.php/dav/addressbooks/users/{debug_data.carddav_username}/contacts/",
        f"{base_url}/carddav/addressbooks/{debug_data.carddav_username}/",
        f"{base_url}/addressbooks/{debug_data.carddav_username}/",
        f"{base_url}/{debug_data.carddav_username}/addressbook.vcf/",
        f"{base_url}/card.php/addressbooks/{debug_data.carddav_username}/default/"
    ]

    return results

# XML phonebook endpoint
@app.get("/phonebook.xml")
async def get_phonebook_xml(db: Session = Depends(get_db)):
    """Generate and serve Grandstream XML phonebook"""
    contacts = db.query(Contact).all()
    groups = db.query(ContactGroup).all()

    xml_content = generate_grandstream_xml(contacts, groups)

    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={
            "Content-Disposition": "inline; filename=phonebook.xml"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
