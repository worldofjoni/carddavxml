import caldav
import vobject
from typing import List, Dict
import logging
import requests
from requests.auth import HTTPBasicAuth, HTTPDigestAuth
import urllib3

logger = logging.getLogger(__name__)

# Disable SSL warnings for self-signed certificates (optional)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class CardDAVClient:
    """
    CardDAV client for fetching contacts from CardDAV server
    """

    def __init__(self, url: str, username: str, password: str, verify_ssl: bool = True):
        self.url = url.rstrip('/')
        self.username = username
        self.password = password
        self.verify_ssl = verify_ssl
        self.client = None
        self.principal = None

    def connect(self):
        """Connect to CardDAV server"""
        logger.info(f"Attempting to connect to CardDAV server: {self.url}")
        logger.info(f"Username: {self.username}")
        logger.info(f"SSL verification: {self.verify_ssl}")

        try:
            # Try with SSL verification first
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password,
                ssl_verify_cert=self.verify_ssl
            )

            logger.info("DAVClient created, attempting to get principal...")

            # Try to get principal
            try:
                self.principal = self.client.principal()
                logger.info("Successfully connected and retrieved principal")
                return True
            except Exception as principal_error:
                logger.error(f"Failed to get principal: {str(principal_error)}")
                logger.info("Trying alternative connection method...")

                # Try direct URL approach
                try:
                    # Some servers need the URL to be the addressbook URL directly
                    import caldav.objects
                    self.principal = caldav.objects.Principal(
                        client=self.client,
                        url=self.url
                    )
                    logger.info("Successfully connected using alternative method")
                    return True
                except Exception as alt_error:
                    logger.error(f"Alternative method also failed: {str(alt_error)}")
                    raise principal_error

        except Exception as e:
            logger.error(f"Failed to connect to CardDAV server: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")

            # Try to provide more helpful error messages
            if "SSL" in str(e) or "certificate" in str(e).lower():
                raise Exception(
                    f"SSL/TLS error: {str(e)}. "
                    "The server may be using a self-signed certificate. "
                    "Try using http:// instead of https:// or configure SSL properly."
                )
            elif "401" in str(e) or "Unauthorized" in str(e):
                raise Exception(
                    f"Authentication failed: {str(e)}. "
                    "Please check your username and password."
                )
            elif "404" in str(e) or "Not Found" in str(e):
                raise Exception(
                    f"URL not found: {str(e)}. "
                    "Please check that the CardDAV URL is correct. "
                    "It should point to the addressbook collection."
                )
            elif "timeout" in str(e).lower():
                raise Exception(
                    f"Connection timeout: {str(e)}. "
                    "Please check that the server is reachable."
                )
            else:
                raise Exception(f"Connection error: {str(e)}")

    def fetch_contacts(self) -> List[Dict]:
        """Fetch all contacts from CardDAV server"""
        if not self.client or not self.principal:
            self.connect()

        contacts = []

        try:
            # Try to get address books
            try:
                address_books = self.principal.addressbooks()
                logger.info(f"Found {len(address_books)} address books")

                for address_book in address_books:
                    logger.info(f"Processing address book: {address_book.url}")
                    # Get all vcards from address book
                    try:
                        vcards = address_book.search(None)
                        logger.info(f"Found {len(vcards)} contacts in address book")

                        for vcard_obj in vcards:
                            try:
                                contact_data = self._parse_vcard(vcard_obj)
                                if contact_data:
                                    contacts.append(contact_data)
                            except Exception as e:
                                logger.warning(f"Failed to parse vcard: {str(e)}")
                                continue

                    except Exception as e:
                        logger.warning(f"Failed to fetch vcards from address book: {str(e)}")
                        continue

            except Exception as addressbook_error:
                logger.warning(f"Could not get addressbooks via principal: {str(addressbook_error)}")
                logger.info("Trying direct addressbook access...")

                # Try direct access if URL points to addressbook
                try:
                    import caldav.objects
                    addressbook = caldav.objects.AddressBook(
                        client=self.client,
                        url=self.url
                    )

                    vcards = addressbook.search(None)
                    logger.info(f"Found {len(vcards)} contacts via direct access")

                    for vcard_obj in vcards:
                        try:
                            contact_data = self._parse_vcard(vcard_obj)
                            if contact_data:
                                contacts.append(contact_data)
                        except Exception as e:
                            logger.warning(f"Failed to parse vcard: {str(e)}")
                            continue

                except Exception as direct_error:
                    logger.error(f"Direct addressbook access also failed: {str(direct_error)}")
                    raise Exception(
                        f"Could not access contacts. "
                        f"Original error: {addressbook_error}. "
                        f"Direct access error: {direct_error}"
                    )

        except Exception as e:
            logger.error(f"Failed to fetch contacts: {str(e)}")
            raise

        logger.info(f"Successfully fetched {len(contacts)} contacts")
        return contacts

    def _parse_vcard(self, vcard_obj) -> Dict:
        """Parse vCard object to contact dictionary"""
        try:
            vcard_data = vcard_obj.data
            vcard = vobject.readOne(vcard_data)

            contact = {
                "first_name": "",
                "last_name": "",
                "is_primary": False,
                "primary": 0,
                "frequent": 0,
                "ringtone": "",
                "photo_url": "",
                "phones": [],
                "emails": [],
                "groups": "",
                "organization": {},
                "address": {},
                "website": "",
                "notes": "",
                "birthday": "",
                "carddav_uid": getattr(vcard, 'uid', None).value if hasattr(vcard, 'uid') else "",
                "carddav_etag": getattr(vcard_obj, 'etag', '')
            }

            # Parse name
            if hasattr(vcard, 'n'):
                n = vcard.n.value
                contact["first_name"] = n.given or ""
                contact["last_name"] = n.family or ""
            elif hasattr(vcard, 'fn'):
                # Fallback to formatted name
                full_name = vcard.fn.value
                parts = full_name.split(' ', 1)
                contact["first_name"] = parts[0]
                if len(parts) > 1:
                    contact["last_name"] = parts[1]

            # Parse phone numbers
            if hasattr(vcard, 'tel_list'):
                for tel in vcard.tel_list:
                    phone_type = "Mobile"
                    if hasattr(tel, 'params'):
                        if 'TYPE' in tel.params:
                            types = tel.params['TYPE']
                            if 'WORK' in types:
                                phone_type = "Work"
                            elif 'HOME' in types:
                                phone_type = "Home"
                            elif 'FAX' in types:
                                phone_type = "Work Fax"

                    contact["phones"].append({
                        "type": phone_type,
                        "number": tel.value,
                        "accountindex": -1
                    })

            # Parse emails
            if hasattr(vcard, 'email_list'):
                for email in vcard.email_list:
                    email_type = "Home"
                    if hasattr(email, 'params'):
                        if 'TYPE' in email.params:
                            types = email.params['TYPE']
                            if 'WORK' in types:
                                email_type = "Work"

                    contact["emails"].append({
                        "type": email_type,
                        "email": email.value
                    })

            # Parse organization
            if hasattr(vcard, 'org'):
                org_value = vcard.org.value
                if isinstance(org_value, list):
                    contact["organization"]["company"] = org_value[0] if len(org_value) > 0 else ""
                    contact["organization"]["department"] = org_value[1] if len(org_value) > 1 else ""
                else:
                    contact["organization"]["company"] = str(org_value)

            # Parse title
            if hasattr(vcard, 'title'):
                contact["organization"]["title"] = vcard.title.value

            # Parse address
            if hasattr(vcard, 'adr_list'):
                for adr in vcard.adr_list:
                    adr_value = adr.value
                    contact["address"] = {
                        "street": adr_value.street or "",
                        "city": adr_value.city or "",
                        "state": adr_value.region or "",
                        "postal_code": adr_value.code or "",
                        "country": adr_value.country or ""
                    }
                    break  # Use first address

            # Parse URL/website
            if hasattr(vcard, 'url'):
                contact["website"] = vcard.url.value

            # Parse note
            if hasattr(vcard, 'note'):
                contact["notes"] = vcard.note.value

            # Parse birthday
            if hasattr(vcard, 'bday'):
                birthday = vcard.bday.value
                if hasattr(birthday, 'strftime'):
                    contact["birthday"] = birthday.strftime('%Y-%m-%d')
                else:
                    contact["birthday"] = str(birthday)

            # Parse photo URL
            if hasattr(vcard, 'photo'):
                if hasattr(vcard.photo, 'params') and 'VALUE' in vcard.photo.params:
                    if vcard.photo.params['VALUE'][0] == 'URI':
                        contact["photo_url"] = vcard.photo.value

            return contact

        except Exception as e:
            logger.error(f"Failed to parse vcard: {str(e)}")
            return None
