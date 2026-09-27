# TeamBoard - B2B Knowledge Base API Platform

Backend service for TeamBoard, a B2B knowledge base API platform. Companies integrate this API into their internal developer portals, helpdesks, and chatbots to query curated technical answers while platform admins can monitor search trends and usage across tenants.

---

## Tech Stack
- **Framework:** Python 3.12, Django 6.1, Django REST Framework
- **Auth:** `djangorestframework-simplejwt` (JWT bearer authentication)
- **Database:** PostgreSQL (via Docker) with fallback/dev support for SQLite
- **Environment:** `python-dotenv` for managing environment variables

---

## Project Structure
```text
.
├── api/
│   ├── management/commands/
│   │   └── seed_kb.py        # Management command to populate sample KB entries
│   ├── migrations/           # Django database migrations
│   ├── admin.py              # Django admin registrations
│   ├── apps.py               # App config & signals registration
│   ├── models.py             # Company, KBEntry, QueryLog models
│   ├── permissions.py        # Custom IsAdminUser permission
│   ├── serializers.py        # Request & response serializers
│   ├── signals.py            # post_save signal auto-creating Company & api_key
│   ├── tests.py              # Automated test suite (all 11 assignment scenarios)
│   ├── urls.py               # API route definitions
│   └── views.py              # API views
├── ScreenShorts/             # Postman test execution screenshots
│   ├── 01 - Register a new company.png
│   ├── 02 - Register with duplicate username.png
│   ├── 03 - Login with valid credentials.png
│   ├── 04 - Login with wrong password.png
│   ├── 05 - Query KB - no token.png
│   ├── 06 - Query KB - valid token with results.png
│   ├── 07 - Query KB - no matching results.png
│   ├── 08 - Query KB - missing search field.png
│   ├── 09 - Usage summary - CLIENT token.png
│   ├── 10 - Setup Admin Account (Helper).png
│   └── 11 - Login as Admin (Helper).png
├── teamboard/
│   ├── settings.py           # Global settings, JWT config & database setup
│   ├── urls.py               # Root URL configuration
│   └── wsgi.py
├── docker-compose.yml        # PostgreSQL service definition
├── requirements.txt          # Pinned dependencies
├── TeamBoard_API_Collection.postman_collection.json # Exported Postman test suite
└── README.md
```

---

## Getting Started

### 1. Clone & install dependencies
Create and activate a virtual environment, then install the pinned requirements:
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Linux / macOS:
source .venv/bin/activate

pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file from the provided `.env.example`:
```bash
# Windows:
copy .env.example .env

# Linux / macOS:
cp .env.example .env
```

Your `.env` file should look like this:
```env
SECRET_KEY=django-insecure-teamboard-secret-key-3289hfdsuif98342784y2834
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*

# For PostgreSQL with Docker:
DB_ENGINE=django.db.backends.postgresql
DB_NAME=teamboard_db
DB_USER=teamboard_user
DB_PASSWORD=teamboard_password
DB_HOST=localhost
DB_PORT=5432

# Or for quick local testing with SQLite without Docker:
# DB_ENGINE=django.db.backends.sqlite3
```

---

## Database Setup

### Option A: Running PostgreSQL via Docker (Recommended)
Start the PostgreSQL container:
```bash
docker compose up -d
```

### Option B: Local SQLite (No Docker required)
Set `DB_ENGINE=django.db.backends.sqlite3` in your `.env` file.

---

## Migrations & Seeding

### 1. Run migrations
Apply database schema migrations:
```bash
python manage.py migrate
```

### 2. Seed Knowledge Base entries
Run the management command to load 13 technical Q&A entries across all categories (API, Database, Cloud, Framework, General):
```bash
python manage.py seed_kb
```

### 3. Create Admin Superuser (Optional)
To log in to the Django admin panel:
```bash
python manage.py createsuperuser
```

---

## Running the Development Server

Start the Django server:
```bash
python manage.py runserver
```
The server will start on `http://127.0.0.1:8000/`.

---

## Running Automated Tests

Run the test suite to verify all endpoints, signals, role permissions, and atomic logging:
```bash
python manage.py test api
```
All 12 test cases test the exact 11 scenarios specified in the assignment.

---

## API Documentation

### 1. Register a Company
- **URL:** `POST /api/auth/register/`
- **Auth:** Public
- **Request Body:**
```json
{
  "username": "acmecorp",
  "password": "securepass123",
  "company_name": "Acme Corp",
  "email": "dev@acmecorp.com"
}
```
- **Response (`201 Created`):**
```json
{
  "username": "acmecorp",
  "company_name": "Acme Corp",
  "api_key": "xY89...auto-generated...",
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```
*Note: A `post_save` signal on the User model creates the Company profile and generates the 32-byte URL-safe `api_key`. The company role always defaults to `client`.*

---

### 2. Login
- **URL:** `POST /api/auth/login/`
- **Auth:** Public
- **Request Body:**
```json
{
  "username": "acmecorp",
  "password": "securepass123"
}
```
- **Response (`200 OK`):**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "company_name": "Acme Corp",
  "api_key": "xY89..."
}
```
*Returns `401 Unauthorized` if credentials are invalid.*

---

### 3. Query Knowledge Base
- **URL:** `POST /api/kb/query/`
- **Auth:** Protected (`Authorization: Bearer <access_token>`)
- **Request Body:**
```json
{
  "search": "select_related"
}
```
- **Response (`200 OK`):**
```json
{
  "search": "select_related",
  "count": 2,
  "results": [
    {
      "id": 1,
      "question": "What is select_related in Django ORM?",
      "answer": "select_related performs a SQL JOIN and fetches related single-valued relationships...",
      "category": "database"
    }
  ]
}
```
*Features:*
- Case-insensitive search on both question and answer fields using `Q(question__icontains=...) | Q(answer__icontains=...)`.
- The search and `QueryLog` insertion run together inside an atomic block (`transaction.atomic()`).
- Returns `count: 0` and empty `results: []` when no matches are found, and still records the query log.
- Returns `400 Bad Request` if the search term is missing or empty.

---

### 4. Admin Usage Summary
- **URL:** `GET /api/admin/usage-summary/`
- **Auth:** Protected (`Authorization: Bearer <admin_access_token>`)
- **Response (`200 OK`):**
```json
{
  "total_queries": 284,
  "active_companies": 7,
  "top_search_terms": [
    { "search_term": "select_related", "count": 42 },
    { "search_term": "transaction atomic", "count": 31 },
    { "search_term": "JWT authentication", "count": 28 },
    { "search_term": "Q objects", "count": 19 },
    { "search_term": "signals django", "count": 14 }
  ]
}
```
*Enforces admin-only access using a custom `IsAdminUser` permission checking `request.user.company.role == 'admin'`. Regular client users receive `403 Forbidden`.*

---

## Postman Collection Testing

The file `TeamBoard_API_Collection.postman_collection.json` contains all 11 test scenarios ready to run:

1. **Import to Postman:**
   - Open Postman, click **Import** and select `TeamBoard_API_Collection.postman_collection.json`.
2. **Execute requests in sequence:**
   - **Scenario 1:** Register a new company (`201` + token saved to collection variables)
   - **Scenario 2:** Register duplicate username (`400`)
   - **Scenario 3:** Login with valid credentials (`200`)
   - **Scenario 4:** Login with wrong password (`401`)
   - **Scenario 5:** Query KB without token (`401`)
   - **Scenario 6:** Query KB with keyword matching entries (`200` + results)
   - **Scenario 7:** Query KB with no matching results (`200` + count 0 + logged)
   - **Scenario 8:** Query KB with missing search field (`400`)
   - **Scenario 9:** Admin usage summary with client token (`403`)
   - **Scenario 10:** Admin usage summary with admin token (`200` + stats)
   - **Scenario 11:** Verify query logs in database / summary count

---

## Screenshots
Test execution screenshots covering all test scenarios are organized in the [`ScreenShorts/`](ScreenShorts/) directory:
- `01 - Register a new company.png`
- `02 - Register with duplicate username.png`
- `03 - Login with valid credentials.png`
- `04 - Login with wrong password.png`
- `05 - Query KB - no token.png`
- `06 - Query KB - valid token with results.png`
- `07 - Query KB - no matching results.png`
- `08 - Query KB - missing search field.png`
- `09 - Usage summary - CLIENT token.png`
- `10 - Setup Admin Account (Helper).png`
- `11 - Login as Admin (Helper).png`
