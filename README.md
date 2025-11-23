# CardDAV to XML Phonebook

A comprehensive Docker-based application that converts CardDAV contacts to Grandstream XML phonebook format, with a modern web UI for managing contacts.

## Features

- **CardDAV Integration**: Sync contacts from any CardDAV-compliant server (Nextcloud, iCloud, Google Contacts, etc.)
- **Grandstream XML Export**: Automatically generates XML phonebook in Grandstream format
- **Web UI**: Modern, responsive interface for managing contacts and groups
- **HTTP Server**: Serves XML phonebook that can be accessed directly by Grandstream phones
- **Contact Management**: Full CRUD operations for contacts with support for:
  - Multiple phone numbers
  - Multiple email addresses
  - Organization details
  - Postal addresses
  - Websites, notes, birthdays
  - Contact groups
  - Custom ringtones
- **Group Management**: Organize contacts into groups
- **Docker Deployment**: Easy deployment with Docker Compose

## Quick Start

### Prerequisites

- Docker
- Docker Compose

### Installation

1. Clone this repository:
```bash
git clone <repository-url>
cd carddavxml
```

2. Start the application:
```bash
docker-compose up -d
```

3. Access the web UI:
```
http://localhost:3000
```

4. The API will be available at:
```
http://localhost:8000
```

5. The XML phonebook will be available at:
```
http://localhost:8000/phonebook.xml
```

## Configuration

### CardDAV Server Setup

1. Navigate to the **Settings** page in the web UI
2. Enter your CardDAV server details:
   - **Server URL**: Full CardDAV URL (e.g., `https://nextcloud.example.com/remote.php/dav/addressbooks/users/username/contacts/`)
   - **Username**: Your CardDAV username
   - **Password**: Your CardDAV password
3. Click **Test Connection** to verify the settings
4. Click **Save Settings** to save your configuration

### Sync Contacts

1. On the **Settings** page, click **Sync Now** to import contacts from your CardDAV server
2. Optionally, check **Clear existing contacts before sync** to replace all contacts
3. The sync will import all contacts and their details

### Configure Grandstream Phone

1. Access your Grandstream phone's web interface
2. Navigate to **Phonebook** → **XML Phonebook**
3. Add a new phonebook entry:
   - **Name**: Any name (e.g., "My Contacts")
   - **URL**: `http://<your-server-ip>:8000/phonebook.xml`
4. Save and the phone will download the phonebook

## Usage

### Managing Contacts

#### Add a Contact
1. Click **Add Contact** on the Contacts page
2. Fill in the contact details
3. Add multiple phone numbers and emails using the **+ Add** buttons
4. Assign to groups by entering comma-separated group IDs
5. Click **Create Contact**

#### Edit a Contact
1. Click **Edit** on any contact card
2. Modify the details
3. Click **Update Contact**

#### Delete a Contact
1. Click **Delete** on any contact card
2. Confirm the deletion

### Managing Groups

1. Navigate to the **Groups** page
2. Click **Add Group** to create a new group
3. Enter the group name and optional ringtone path
4. Groups can be assigned to contacts using their ID

### XML Phonebook Format

The application generates XML in Grandstream format with support for:

- **Contact Information**: First name, last name
- **Phone Numbers**: Multiple numbers with types (Mobile, Home, Work, Fax)
- **Email Addresses**: Multiple emails with types
- **Organization**: Company name, job title, department
- **Address**: Street, city, state, postal code, country
- **Additional Data**: Website, notes, birthday, ringtone, photo URL
- **Groups**: Contact group memberships

## Architecture

### Backend (Python FastAPI)

- **FastAPI**: Modern, fast web framework
- **SQLAlchemy**: Database ORM
- **caldav**: CardDAV client library
- **vobject**: vCard parsing
- **lxml**: XML generation

### Frontend (React TypeScript)

- **React 18**: Modern UI library
- **TypeScript**: Type-safe development
- **React Router**: Client-side routing
- **Axios**: HTTP client

### Database

- **SQLite**: Lightweight, file-based database
- Stores contacts, groups, and settings

## API Endpoints

### Contacts
- `GET /api/contacts` - List all contacts
- `GET /api/contacts/{id}` - Get a specific contact
- `POST /api/contacts` - Create a new contact
- `PUT /api/contacts/{id}` - Update a contact
- `DELETE /api/contacts/{id}` - Delete a contact

### Groups
- `GET /api/groups` - List all groups
- `POST /api/groups` - Create a new group
- `DELETE /api/groups/{id}` - Delete a group

### Settings
- `GET /api/settings` - Get CardDAV settings
- `PUT /api/settings` - Update settings

### Sync
- `POST /api/sync/carddav` - Sync contacts from CardDAV
- `POST /api/sync/test` - Test CardDAV connection

### Phonebook
- `GET /phonebook.xml` - Download Grandstream XML phonebook

## Development

### Backend Development

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm start
```

### Environment Variables

#### Backend
- `DATABASE_URL`: Database connection string (default: `sqlite:///data/carddav.db`)
- `CORS_ORIGINS`: Allowed CORS origins

#### Frontend
- `REACT_APP_API_URL`: Backend API URL (default: `http://localhost:8000`)

## Supported CardDAV Servers

- **Nextcloud**: Full support
- **iCloud**: Full support
- **Google Contacts**: Via CardDAV API
- **Synology**: CardDAV Server package
- **Radicale**: Lightweight CalDAV/CardDAV server
- **Baïkal**: Lightweight CalDAV/CardDAV server
- Any RFC-compliant CardDAV server

## Data Persistence

Contact data is stored in a SQLite database located at `/app/data/carddav.db` in the backend container. This is mounted as a Docker volume to persist data across container restarts.

## Troubleshooting

### CardDAV Connection Issues

1. Verify the CardDAV URL is correct and includes the full path
2. Check username and password
3. Ensure the CardDAV server is accessible from the Docker container
4. Check the backend logs: `docker-compose logs backend`

### XML Phonebook Not Loading on Phone

1. Verify the URL is accessible from the phone's network
2. Check that port 8000 is accessible from your network
3. Ensure the XML format is correct by viewing it in a browser

### Port Conflicts

If ports 3000 or 8000 are already in use, modify the `docker-compose.yml` file:

```yaml
ports:
  - "8080:8000"  # Change 8000 to 8080
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.
