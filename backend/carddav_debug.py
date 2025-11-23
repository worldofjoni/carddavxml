#!/usr/bin/env python3
"""
CardDAV Connection Debugger
This script helps diagnose CardDAV connection issues
"""

import sys
import logging
import caldav
import requests
from requests.auth import HTTPBasicAuth

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_http_basic(url, username, password):
    """Test basic HTTP connectivity"""
    print("\n" + "="*60)
    print("1. Testing Basic HTTP Connectivity")
    print("="*60)

    try:
        response = requests.get(
            url,
            auth=HTTPBasicAuth(username, password),
            timeout=10,
            verify=False  # Disable SSL verification for testing
        )
        print(f"✓ HTTP Status: {response.status_code}")
        print(f"✓ Server: {response.headers.get('Server', 'Unknown')}")
        print(f"✓ DAV Header: {response.headers.get('DAV', 'Not present')}")
        return True
    except requests.exceptions.SSLError as e:
        print(f"✗ SSL Error: {e}")
        print("  → Try using http:// instead of https://")
        return False
    except requests.exceptions.Timeout:
        print("✗ Connection timeout")
        print("  → Server is not reachable")
        return False
    except requests.exceptions.ConnectionError as e:
        print(f"✗ Connection Error: {e}")
        print("  → Check if server is running and URL is correct")
        return False
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_dav_options(url, username, password):
    """Test DAV OPTIONS request"""
    print("\n" + "="*60)
    print("2. Testing DAV OPTIONS")
    print("="*60)

    try:
        response = requests.request(
            'OPTIONS',
            url,
            auth=HTTPBasicAuth(username, password),
            timeout=10,
            verify=False
        )
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Allow: {response.headers.get('Allow', 'Not present')}")
        print(f"✓ DAV: {response.headers.get('DAV', 'Not present')}")

        if 'addressbook' in response.headers.get('DAV', '').lower():
            print("✓ Server supports CardDAV!")
        else:
            print("⚠ CardDAV support unclear from headers")

        return True
    except Exception as e:
        print(f"✗ Error: {e}")
        return False


def test_caldav_client(url, username, password):
    """Test caldav library connection"""
    print("\n" + "="*60)
    print("3. Testing caldav Library Connection")
    print("="*60)

    try:
        print(f"Connecting to: {url}")
        print(f"Username: {username}")

        client = caldav.DAVClient(
            url=url,
            username=username,
            password=password,
            ssl_verify_cert=False
        )
        print("✓ DAVClient created")

        try:
            principal = client.principal()
            print(f"✓ Principal: {principal.url}")

            try:
                addressbooks = principal.addressbooks()
                print(f"✓ Found {len(addressbooks)} addressbooks:")
                for ab in addressbooks:
                    print(f"  - {ab.url}")
                return True
            except Exception as e:
                print(f"⚠ Could not list addressbooks: {e}")
                print("  → URL might point directly to an addressbook")

                # Try direct addressbook access
                try:
                    import caldav.objects
                    addressbook = caldav.objects.AddressBook(
                        client=client,
                        url=url
                    )
                    contacts = addressbook.search(None)
                    print(f"✓ Direct addressbook access works! Found {len(contacts)} contacts")
                    return True
                except Exception as e2:
                    print(f"✗ Direct addressbook access failed: {e2}")
                    return False

        except Exception as e:
            print(f"✗ Could not get principal: {e}")
            print("\nPossible issues:")
            print("  1. URL should end with the user's principal path")
            print("  2. For Nextcloud: /remote.php/dav/addressbooks/users/USERNAME/")
            print("  3. For iCloud: Check iCloud-specific CardDAV URL format")
            print("  4. Some servers need the addressbook URL directly")
            return False

    except Exception as e:
        print(f"✗ Failed to create DAVClient: {e}")
        return False


def suggest_url_formats(url, username):
    """Suggest possible URL formats"""
    print("\n" + "="*60)
    print("4. Suggested URL Formats")
    print("="*60)

    from urllib.parse import urlparse
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    suggestions = [
        # Nextcloud/ownCloud
        f"{base_url}/remote.php/dav/addressbooks/users/{username}/",
        f"{base_url}/remote.php/dav/addressbooks/users/{username}/contacts/",

        # Generic
        f"{base_url}/carddav/addressbooks/{username}/",
        f"{base_url}/addressbooks/{username}/",

        # Radicale
        f"{base_url}/{username}/addressbook.vcf/",

        # Baikal
        f"{base_url}/card.php/addressbooks/{username}/default/",
    ]

    print("\nTry these URLs:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. {suggestion}")


def main():
    print("="*60)
    print("CardDAV Connection Debugger")
    print("="*60)

    if len(sys.argv) != 4:
        print("\nUsage: python carddav_debug.py <URL> <USERNAME> <PASSWORD>")
        print("\nExample:")
        print("  python carddav_debug.py https://cloud.example.com/remote.php/dav/addressbooks/users/john/ john mypassword")
        sys.exit(1)

    url = sys.argv[1]
    username = sys.argv[2]
    password = sys.argv[3]

    print(f"\nTesting connection to: {url}")
    print(f"Username: {username}")
    print(f"Password: {'*' * len(password)}")

    # Run tests
    http_ok = test_http_basic(url, username, password)

    if http_ok:
        test_dav_options(url, username, password)

    caldav_ok = test_caldav_client(url, username, password)

    if not caldav_ok:
        suggest_url_formats(url, username)

    print("\n" + "="*60)
    print("Summary")
    print("="*60)

    if caldav_ok:
        print("✓ CardDAV connection successful!")
        print("  You can use this URL in the application.")
    else:
        print("✗ CardDAV connection failed")
        print("\nTroubleshooting steps:")
        print("1. Verify the URL is correct")
        print("2. Check username and password")
        print("3. Try the suggested URL formats above")
        print("4. Check server logs for more details")
        print("5. Ensure CardDAV is enabled on the server")


if __name__ == "__main__":
    main()
