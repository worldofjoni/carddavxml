from lxml import etree
from typing import List
from models import Contact, ContactGroup


def generate_grandstream_xml(contacts: List[Contact], groups: List[ContactGroup]) -> str:
    """
    Generate Grandstream XML phonebook from contacts and groups
    """
    # Create root element
    root = etree.Element("AddressBook")

    # Add version
    version = etree.SubElement(root, "version")
    version.text = "1"

    # Add contact groups
    for group in groups:
        pbgroup = etree.SubElement(root, "pbgroup")

        group_id = etree.SubElement(pbgroup, "id")
        group_id.text = str(group.id)

        group_name = etree.SubElement(pbgroup, "name")
        group_name.text = group.name

        ringtones = etree.SubElement(pbgroup, "ringtones")
        if group.ringtones:
            ringtones.text = group.ringtones

    # Add contacts
    for contact in contacts:
        contact_elem = etree.SubElement(root, "Contact")

        # Basic info
        first_name = etree.SubElement(contact_elem, "FirstName")
        first_name.text = contact.first_name or ""

        last_name = etree.SubElement(contact_elem, "LastName")
        last_name.text = contact.last_name or ""

        is_primary = etree.SubElement(contact_elem, "IsPrimary")
        is_primary.text = "true" if contact.is_primary else "false"

        primary = etree.SubElement(contact_elem, "Primary")
        primary.text = str(contact.primary)

        frequent = etree.SubElement(contact_elem, "Frequent")
        frequent.text = str(contact.frequent)

        # Ringtone
        if contact.ringtone:
            ringtone = etree.SubElement(contact_elem, "Ringtone")
            ringtone.text = contact.ringtone

        # Photo URL
        photo_url = etree.SubElement(contact_elem, "PhotoUrl")
        if contact.photo_url:
            photo_url.text = contact.photo_url

        # Phone numbers
        if contact.phones:
            for phone_data in contact.phones:
                phone = etree.SubElement(contact_elem, "Phone")
                phone.set("type", phone_data.get("type", "Mobile"))

                phonenumber = etree.SubElement(phone, "phonenumber")
                phonenumber.text = phone_data.get("number", "")

                accountindex = etree.SubElement(phone, "accountindex")
                accountindex.text = str(phone_data.get("accountindex", -1))

        # Email addresses
        if contact.emails:
            for email_data in contact.emails:
                mail = etree.SubElement(contact_elem, "Mail")
                mail.set("type", email_data.get("type", "Home"))
                mail.text = email_data.get("email", "")

        # Groups
        if contact.groups:
            group_ids = contact.groups.split(",")
            for group_id in group_ids:
                if group_id.strip():
                    group_elem = etree.SubElement(contact_elem, "Group")
                    group_elem.text = group_id.strip()

        # Organization as extra_element
        if contact.organization and any(contact.organization.values()):
            org_elem = etree.SubElement(contact_elem, "extra_element")
            org_elem.set("mimetype", "vnd.android.cursor.item/organization")

            if contact.organization.get("company"):
                data_company = etree.SubElement(org_elem, "data")
                data_company.set("column", "data1")
                data_company.text = contact.organization["company"]

            mimetype = etree.SubElement(org_elem, "data")
            mimetype.set("column", "mimetype")
            mimetype.text = "vnd.android.cursor.item/organization"

            if contact.organization.get("title"):
                data_title = etree.SubElement(org_elem, "data")
                data_title.set("column", "data4")
                data_title.text = contact.organization["title"]

            if contact.organization.get("department"):
                data_dept = etree.SubElement(org_elem, "data")
                data_dept.set("column", "data5")
                data_dept.text = contact.organization["department"]

        # Address as extra_element
        if contact.address and any(contact.address.values()):
            addr_elem = etree.SubElement(contact_elem, "extra_element")
            addr_elem.set("mimetype", "vnd.android.cursor.item/postal-address_v2")

            # Build full address
            address_parts = []
            if contact.address.get("street"):
                address_parts.append(contact.address["street"])
            if contact.address.get("city"):
                address_parts.append(contact.address["city"])
            if contact.address.get("state"):
                address_parts.append(contact.address["state"])

            full_address = "\n".join(address_parts)

            # data9 - postal code
            if contact.address.get("postal_code"):
                data9 = etree.SubElement(addr_elem, "data")
                data9.set("column", "data9")
                data9.text = contact.address["postal_code"]

            # data5 - (empty in examples)
            data5 = etree.SubElement(addr_elem, "data")
            data5.set("column", "data5")

            # data8 - state
            if contact.address.get("state"):
                data8 = etree.SubElement(addr_elem, "data")
                data8.set("column", "data8")
                data8.text = contact.address["state"]

            # data1 - full address
            if full_address:
                data1 = etree.SubElement(addr_elem, "data")
                data1.set("column", "data1")
                data1.text = full_address

            # data6 - (empty in examples)
            data6 = etree.SubElement(addr_elem, "data")
            data6.set("column", "data6")

            # data2 - type (1 = home, 2 = work)
            data2 = etree.SubElement(addr_elem, "data")
            data2.set("column", "data2")
            data2.text = "1"

            # data4 - street
            if contact.address.get("street"):
                data4 = etree.SubElement(addr_elem, "data")
                data4.set("column", "data4")
                data4.text = contact.address["street"]

            # data10 - country
            if contact.address.get("country"):
                data10 = etree.SubElement(addr_elem, "data")
                data10.set("column", "data10")
                data10.text = contact.address["country"]

            # mimetype
            mimetype = etree.SubElement(addr_elem, "data")
            mimetype.set("column", "mimetype")
            mimetype.text = "vnd.android.cursor.item/postal-address_v2"

            # data7 - city
            if contact.address.get("city"):
                data7 = etree.SubElement(addr_elem, "data")
                data7.set("column", "data7")
                data7.text = contact.address["city"]

        # Website as extra_element
        if contact.website:
            web_elem = etree.SubElement(contact_elem, "extra_element")
            web_elem.set("mimetype", "vnd.android.cursor.item/website")

            data1 = etree.SubElement(web_elem, "data")
            data1.set("column", "data1")
            data1.text = contact.website

            data2 = etree.SubElement(web_elem, "data")
            data2.set("column", "data2")
            data2.text = "7"

            mimetype = etree.SubElement(web_elem, "data")
            mimetype.set("column", "mimetype")
            mimetype.text = "vnd.android.cursor.item/website"

        # Notes as extra_element
        if contact.notes:
            note_elem = etree.SubElement(contact_elem, "extra_element")
            note_elem.set("mimetype", "vnd.android.cursor.item/note")

            data1 = etree.SubElement(note_elem, "data")
            data1.set("column", "data1")
            data1.text = contact.notes

            mimetype = etree.SubElement(note_elem, "data")
            mimetype.set("column", "mimetype")
            mimetype.text = "vnd.android.cursor.item/note"

        # Birthday as extra_element
        if contact.birthday:
            event_elem = etree.SubElement(contact_elem, "extra_element")
            event_elem.set("mimetype", "vnd.android.cursor.item/contact_event")

            data1 = etree.SubElement(event_elem, "data")
            data1.set("column", "data1")
            data1.text = contact.birthday

            data2 = etree.SubElement(event_elem, "data")
            data2.set("column", "data2")
            data2.text = "3"  # 3 = birthday

            mimetype = etree.SubElement(event_elem, "data")
            mimetype.set("column", "mimetype")
            mimetype.text = "vnd.android.cursor.item/contact_event"

    # Generate XML string
    xml_string = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='UTF-8',
        standalone=False
    )

    return xml_string.decode('utf-8')
