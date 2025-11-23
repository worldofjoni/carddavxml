"""
Background sync scheduler for automatic CardDAV synchronization
"""

import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from database import SessionLocal
from models import Settings, Contact
from carddav_client import CardDAVClient

logger = logging.getLogger(__name__)

# Global scheduler instance
scheduler = BackgroundScheduler()
current_job = None


def perform_sync():
    """
    Perform CardDAV synchronization
    This function is called by the scheduler
    """
    db = SessionLocal()
    try:
        # Get settings
        settings = db.query(Settings).first()

        if not settings:
            logger.warning("No settings found, skipping sync")
            return

        if not settings.sync_enabled:
            logger.info("Auto-sync is disabled, skipping")
            return

        if not settings.carddav_url or not settings.carddav_username:
            logger.warning("CardDAV credentials not configured, skipping sync")
            return

        # Update status to running
        settings.last_sync = datetime.utcnow().isoformat()
        settings.last_sync_status = "running"
        settings.last_sync_message = "Synchronization in progress..."
        db.commit()

        logger.info(f"Starting automatic CardDAV sync from {settings.carddav_url}")

        try:
            # Create CardDAV client
            client = CardDAVClient(
                url=settings.carddav_url,
                username=settings.carddav_username,
                password=settings.carddav_password,
                verify_ssl=True  # Default to True for auto-sync
            )

            # Fetch contacts
            contacts = client.fetch_contacts()

            logger.info(f"Fetched {len(contacts)} contacts from CardDAV server")

            # Update existing contacts and add new ones
            # We'll match by carddav_uid to avoid duplicates
            updated_count = 0
            added_count = 0

            for contact_data in contacts:
                carddav_uid = contact_data.get('carddav_uid', '')

                if carddav_uid:
                    # Try to find existing contact by UID
                    existing = db.query(Contact).filter(
                        Contact.carddav_uid == carddav_uid
                    ).first()

                    if existing:
                        # Update existing contact
                        for key, value in contact_data.items():
                            setattr(existing, key, value)
                        updated_count += 1
                    else:
                        # Add new contact
                        db_contact = Contact(**contact_data)
                        db.add(db_contact)
                        added_count += 1
                else:
                    # No UID, just add as new
                    db_contact = Contact(**contact_data)
                    db.add(db_contact)
                    added_count += 1

            db.commit()

            # Update status to success
            message = f"Successfully synced: {added_count} new, {updated_count} updated"
            settings.last_sync_status = "success"
            settings.last_sync_message = message
            db.commit()

            logger.info(message)

        except Exception as e:
            error_msg = f"Sync failed: {str(e)}"
            logger.error(error_msg)

            # Update status to failed
            settings.last_sync_status = "failed"
            settings.last_sync_message = error_msg
            db.commit()

    except Exception as e:
        logger.error(f"Error in sync job: {str(e)}")
    finally:
        db.close()


def update_scheduler():
    """
    Update the scheduler based on current settings
    This should be called whenever settings are changed
    """
    global current_job

    db = SessionLocal()
    try:
        settings = db.query(Settings).first()

        if not settings:
            logger.info("No settings found, scheduler not started")
            return

        # Remove existing job if any
        if current_job:
            try:
                scheduler.remove_job(current_job.id)
                logger.info(f"Removed existing sync job: {current_job.id}")
            except:
                pass
            current_job = None

        # Add new job if sync is enabled
        if settings.sync_enabled and settings.carddav_url:
            interval_seconds = max(settings.auto_sync_interval, 60)  # Minimum 1 minute

            current_job = scheduler.add_job(
                perform_sync,
                trigger=IntervalTrigger(seconds=interval_seconds),
                id='carddav_sync',
                name='CardDAV Auto Sync',
                replace_existing=True
            )

            logger.info(
                f"Scheduled CardDAV sync every {interval_seconds} seconds "
                f"({interval_seconds / 60:.1f} minutes)"
            )
        else:
            logger.info("Auto-sync is disabled or not configured")

    except Exception as e:
        logger.error(f"Error updating scheduler: {str(e)}")
    finally:
        db.close()


def start_scheduler():
    """
    Start the background scheduler
    This should be called when the application starts
    """
    if not scheduler.running:
        scheduler.start()
        logger.info("Background scheduler started")

        # Initialize the sync job based on current settings
        update_scheduler()


def stop_scheduler():
    """
    Stop the background scheduler
    This should be called when the application shuts down
    """
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Background scheduler stopped")
