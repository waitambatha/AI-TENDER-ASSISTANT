# Starting Tender AI Assistant Services

## Prerequisites
1. **Start Docker Desktop**
   - Open Docker Desktop application
   - Wait for it to fully start (green status indicator)

## Step-by-Step Startup

### 1. Start Weaviate (Vector Database)
```bash
cd /home/sly/PycharmProjects/tender
docker compose up -d
```

### 2. Verify Weaviate is Running
```bash
curl http://localhost:8080/v1/meta
```
You should see JSON response with Weaviate metadata.

### 3. Start Django Development Server
```bash
cd /home/sly/PycharmProjects/tender
source venv/bin/activate
python manage.py runserver
```

### 4. Access the Application
- **Admin Dashboard:** http://127.0.0.1:8000/dashboard/
- **User Login:** http://127.0.0.1:8000/users/login/

## Default Credentials
- **Admin Username:** admin
- **Admin Password:** masterclass

## New Features Available

### For Users:
1. **Document Search Dashboard**
   - Search through processed document summaries
   - Results cached to avoid token waste
   - View search history

2. **Custom AI API Keys**
   - Add your own OpenAI API keys
   - Switch between default and custom keys
   - Encrypted storage for security

3. **Search Logs**
   - View all previous searches
   - Cached results for efficiency
   - No duplicate API calls

### For Admins:
- All existing features remain unchanged
- Document processing now integrates with Weaviate
- Enhanced search capabilities

## Troubleshooting

### Weaviate Connection Issues
```bash
# Check if Weaviate is running
docker ps

# View Weaviate logs
docker compose logs weaviate

# Restart Weaviate
docker compose restart weaviate
```

### Django Issues
```bash
# Check migrations
python manage.py showmigrations

# Apply any pending migrations
python manage.py migrate

# Create superuser if needed
python manage.py createsuperuser
```

## Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Django App    │────│   PostgreSQL     │    │   Weaviate      │
│   (Port 8000)   │    │   (Database)     │    │   (Port 8080)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
    ┌────▼────┐             ┌────▼────┐             ┌────▼────┐
    │ User    │             │ Search  │             │Document │
    │ Mgmt    │             │ Logs    │             │Summaries│
    │ API Keys│             │ Cache   │             │ Vector  │
    └─────────┘             └─────────┘             │ Search  │
                                                    └─────────┘
```

## Environment Variables
Make sure your `.env` file contains:
```
DB_NAME=tender_project
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
OPENAI_API_KEY=your_openai_api_key
ENCRYPTION_KEY=5c-eQU449hNZC9T6TWRoAw-O7LmyR9yLbI3AFohxi0s=
```
