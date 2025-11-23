import caldav
import vobject
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class CardDAVClient:
    """
    CardDAV client for fetching contacts from CardDAV server
    """

    def __init__(self, url: str, username: str, password: str):
        self.url = url
        self.username = username
        self.password = password
        self.client = None
        self.principal = None

    def connect(self):
        """Connect to CardDAV server"""
        try:
            self.client = caldav.DAVClient(
                url=self.url,
                username=self.username,
                password=self.password
            )
            self.principal = self.client.principal()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to CardDAV server: {str(e)}")
            raise

    def fetch_contacts(self) -> List[Dict]:
        """Fetch all contacts from CardDAV server"""
        if not self.client or not self.principal:
            self.connect()

        contacts = []

        try:
            # Get address books
            address_books = self.principal.addressbooks()

            for address_book in address_books:
                # Get all vcards from address book
                try:
                    vcards = address_book.search(None)

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

        except Exception as e:
            logger.error(f"Failed to fetch contacts: {str(e)}")
            raise

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
