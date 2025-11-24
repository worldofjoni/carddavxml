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
        """Fetch all contacts from CardDAV server using raw HTTP requests"""
        if not self.client:
            self.connect()

        contacts = []

        try:
            logger.info("Fetching contacts using CardDAV protocol...")

            # Use raw HTTP requests since caldav library is for CalDAV, not CardDAV
            # CardDAV REPORT query to get all vcards
            report_body = '''<?xml version="1.0" encoding="utf-8" ?>
<C:addressbook-query xmlns:D="DAV:" xmlns:C="urn:ietf:params:xml:ns:carddav">
  <D:prop>
    <D:getetag/>
    <C:address-data/>
  </D:prop>
</C:addressbook-query>'''

            headers = {
                'Content-Type': 'application/xml; charset=utf-8',
                'Depth': '1'
            }

            auth = HTTPBasicAuth(self.username, self.password)

            logger.info(f"Sending REPORT request to {self.url}")
            response = requests.request(
                'REPORT',
                self.url,
                data=report_body,
                headers=headers,
                auth=auth,
                verify=self.verify_ssl
            )

            logger.info(f"REPORT response status: {response.status_code}")

            if response.status_code == 207:  # Multi-Status
                # Parse the XML response
                import xml.etree.ElementTree as ET
                root = ET.fromstring(response.content)

                # Define namespaces
                ns = {
                    'D': 'DAV:',
                    'C': 'urn:ietf:params:xml:ns:carddav'
                }

                # Find all response elements
                responses = root.findall('.//D:response', ns)
                logger.info(f"Found {len(responses)} vcard responses")

                for resp in responses:
                    try:
                        # Get the vcard data
                        address_data = resp.find('.//C:address-data', ns)
                        if address_data is not None and address_data.text:
                            # Parse vcard
                            vcard = vobject.readOne(address_data.text)

                            # Get etag if available
                            etag_elem = resp.find('.//D:getetag', ns)
                            etag = etag_elem.text if etag_elem is not None else ''

                            # Create a simple object to hold vcard data and etag
                            class VCardObject:
                                def __init__(self, data, etag):
                                    self.data = data
                                    self.etag = etag

                            vcard_obj = VCardObject(address_data.text, etag)
                            contact_data = self._parse_vcard(vcard_obj)
                            if contact_data:
                                contacts.append(contact_data)

                    except Exception as e:
                        logger.warning(f"Failed to parse vcard: {str(e)}")
                        continue

            elif response.status_code == 401:
                raise Exception("Authentication failed. Please check your username and password.")
            elif response.status_code == 404:
                raise Exception("Addressbook not found. Please check the CardDAV URL.")
            else:
                raise Exception(f"CardDAV REPORT failed with status {response.status_code}: {response.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {str(e)}")
            raise Exception(f"Failed to connect to CardDAV server: {str(e)}")
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
