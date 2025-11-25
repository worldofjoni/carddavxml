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
            # Create DAV client
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password,
                ssl_verify_cert=self.verify_ssl
            )

            logger.info("DAVClient created successfully")

            # Try to get principal (optional - we can work without it)
            try:
                self.principal = self.client.principal()
                logger.info("Successfully retrieved principal")
            except Exception as principal_error:
                logger.warning(f"Could not get principal: {str(principal_error)}")
                logger.info("Will attempt direct addressbook access instead")
                # Don't fail here - direct addressbook access can work without principal
                self.principal = None

            return True

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
        if not self.client:
            self.connect()

        contacts = []
        direct_error = None  # Initialize to None for proper scoping

        try:
            # Try direct addressbook access first (works with more server types)
            logger.info("Attempting direct addressbook access...")
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

                # If direct access worked, return early
                if contacts or len(vcards) == 0:
                    logger.info(f"Successfully fetched {len(contacts)} contacts via direct access")
                    return contacts

            except Exception as direct_error:
                logger.warning(f"Direct addressbook access failed: {str(direct_error)}")
                logger.info("Trying principal.addressbooks() method...")

            # Fallback to principal.addressbooks() method
            if self.principal:
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
                    logger.error(f"Could not get addressbooks via principal: {str(addressbook_error)}")
                    direct_msg = str(direct_error) if direct_error else "Unknown error or no contacts found"
                    raise Exception(
                        f"Could not access contacts using any method. "
                        f"Direct access error: {direct_msg}. "
                        f"Principal method error: {addressbook_error}"
                    )
            else:
                direct_msg = str(direct_error) if direct_error else "Unknown error or no contacts found"
                raise Exception(
                    f"Could not access contacts. Direct access failed: {direct_msg}"
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

    def _generate_vcard(self, contact: Dict) -> str:
        """Generate vCard string from contact dictionary"""
        vcard = vobject.vCard()

        # Add name
        vcard.add('n')
        vcard.n.value = vobject.vcard.Name(
            family=contact.get('last_name', ''),
            given=contact.get('first_name', '')
        )

        # Add formatted name
        vcard.add('fn')
        full_name = f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip()
        vcard.fn.value = full_name or contact.get('first_name', 'Unnamed')

        # Add UID if exists
        if contact.get('carddav_uid'):
            vcard.add('uid')
            vcard.uid.value = contact['carddav_uid']

        # Add phone numbers
        for phone in contact.get('phones', []):
            tel = vcard.add('tel')
            tel.value = phone.get('number', '')
            phone_type = phone.get('type', 'Mobile').upper()
            if phone_type == 'MOBILE':
                tel.type_param = ['CELL', 'VOICE']
            elif phone_type == 'HOME':
                tel.type_param = ['HOME', 'VOICE']
            elif phone_type == 'WORK':
                tel.type_param = ['WORK', 'VOICE']
            elif 'FAX' in phone_type:
                tel.type_param = ['WORK', 'FAX']
            else:
                tel.type_param = ['VOICE']

        # Add emails
        for email in contact.get('emails', []):
            email_obj = vcard.add('email')
            email_obj.value = email.get('email', '')
            email_type = email.get('type', 'Home').upper()
            if email_type == 'WORK':
                email_obj.type_param = ['INTERNET', 'WORK']
            else:
                email_obj.type_param = ['INTERNET', 'HOME']

        # Add organization
        org = contact.get('organization', {})
        if org.get('company') or org.get('department'):
            vcard.add('org')
            vcard.org.value = [org.get('company', ''), org.get('department', '')]

        if org.get('title'):
            vcard.add('title')
            vcard.title.value = org.get('title', '')

        # Add address
        address = contact.get('address', {})
        if any(address.values()):
            adr = vcard.add('adr')
            adr.value = vobject.vcard.Address(
                street=address.get('street', ''),
                city=address.get('city', ''),
                region=address.get('state', ''),
                code=address.get('postal_code', ''),
                country=address.get('country', '')
            )
            adr.type_param = ['HOME']

        # Add website
        if contact.get('website'):
            vcard.add('url')
            vcard.url.value = contact['website']

        # Add notes
        if contact.get('notes'):
            vcard.add('note')
            vcard.note.value = contact['notes']

        # Add birthday
        if contact.get('birthday'):
            vcard.add('bday')
            vcard.bday.value = contact['birthday']

        # Add photo URL if exists
        if contact.get('photo_url'):
            vcard.add('photo')
            vcard.photo.value = contact['photo_url']
            vcard.photo.params['VALUE'] = ['URI']

        return vcard.serialize()

    def create_contact(self, contact: Dict) -> Dict:
        """Create a new contact on CardDAV server"""
        if not self.client:
            self.connect()

        try:
            # Generate UID if not present
            if not contact.get('carddav_uid'):
                import uuid
                contact['carddav_uid'] = str(uuid.uuid4())

            # Generate vCard
            vcard_data = self._generate_vcard(contact)

            logger.info(f"Creating contact on CardDAV server: {contact.get('first_name')} {contact.get('last_name')}")

            # Try to get addressbook
            import caldav.objects
            try:
                addressbook = caldav.objects.AddressBook(
                    client=self.client,
                    url=self.url
                )
            except Exception as e:
                # Fallback to principal method
                if self.principal:
                    address_books = self.principal.addressbooks()
                    if address_books:
                        addressbook = address_books[0]
                    else:
                        raise Exception("No addressbooks found")
                else:
                    raise Exception(f"Could not access addressbook: {str(e)}")

            # Create the contact
            vcard_obj = addressbook.add_vcard(vcard_data)

            # Get the etag from created object
            if hasattr(vcard_obj, 'etag'):
                contact['carddav_etag'] = vcard_obj.etag

            logger.info(f"Successfully created contact with UID: {contact['carddav_uid']}")
            return contact

        except Exception as e:
            logger.error(f"Failed to create contact on CardDAV server: {str(e)}")
            raise Exception(f"Failed to create contact on CardDAV server: {str(e)}")

    def update_contact(self, contact: Dict) -> Dict:
        """Update an existing contact on CardDAV server"""
        if not self.client:
            self.connect()

        if not contact.get('carddav_uid'):
            raise Exception("Cannot update contact without carddav_uid")

        try:
            logger.info(f"Updating contact on CardDAV server: {contact.get('carddav_uid')}")

            # Generate vCard
            vcard_data = self._generate_vcard(contact)

            # Get addressbook
            import caldav.objects
            try:
                addressbook = caldav.objects.AddressBook(
                    client=self.client,
                    url=self.url
                )
            except Exception:
                if self.principal:
                    address_books = self.principal.addressbooks()
                    if address_books:
                        addressbook = address_books[0]
                    else:
                        raise Exception("No addressbooks found")
                else:
                    raise

            # Find and update the contact by UID
            vcards = addressbook.search(uid=contact['carddav_uid'])

            if not vcards:
                logger.warning(f"Contact with UID {contact['carddav_uid']} not found, creating new")
                return self.create_contact(contact)

            vcard_obj = vcards[0]
            vcard_obj.data = vcard_data
            vcard_obj.save()

            # Update etag
            if hasattr(vcard_obj, 'etag'):
                contact['carddav_etag'] = vcard_obj.etag

            logger.info(f"Successfully updated contact with UID: {contact['carddav_uid']}")
            return contact

        except Exception as e:
            logger.error(f"Failed to update contact on CardDAV server: {str(e)}")
            raise Exception(f"Failed to update contact on CardDAV server: {str(e)}")

    def delete_contact(self, carddav_uid: str) -> bool:
        """Delete a contact from CardDAV server"""
        if not self.client:
            self.connect()

        if not carddav_uid:
            raise Exception("Cannot delete contact without carddav_uid")

        try:
            logger.info(f"Deleting contact from CardDAV server: {carddav_uid}")

            # Get addressbook
            import caldav.objects
            try:
                addressbook = caldav.objects.AddressBook(
                    client=self.client,
                    url=self.url
                )
            except Exception:
                if self.principal:
                    address_books = self.principal.addressbooks()
                    if address_books:
                        addressbook = address_books[0]
                    else:
                        raise Exception("No addressbooks found")
                else:
                    raise

            # Find and delete the contact
            vcards = addressbook.search(uid=carddav_uid)

            if not vcards:
                logger.warning(f"Contact with UID {carddav_uid} not found on server")
                return False

            vcard_obj = vcards[0]
            vcard_obj.delete()

            logger.info(f"Successfully deleted contact with UID: {carddav_uid}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete contact from CardDAV server: {str(e)}")
            raise Exception(f"Failed to delete contact from CardDAV server: {str(e)}")
