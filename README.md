# Address Book REST API

A FastAPI application for managing addresses with CRUD operations, proximity search using the Haversine formula, pagination, filtering, and validation.

## Live API

- **Swagger UI:** [https://address-manager-whz5.onrender.com/docs](https://address-manager-whz5.onrender.com/docs)
- **ReDoc:** [https://address-manager-whz5.onrender.com/redoc](https://address-manager-whz5.onrender.com/redoc)
- **Health check:** [https://address-manager-whz5.onrender.com/health](https://address-manager-whz5.onrender.com/health)

## Features

- **Full CRUD** — Create, read, update, and delete address records
- **Proximity search** — Find addresses within a radius using the Haversine formula (no GIS libraries)
- **Pagination** — Paginated listing with configurable page size
- **Sorting** — Sort by `name`, `city`, or `created_at` (asc/desc)
- **Filtering** — Filter by country and search by name/city
- **Validation** — Pydantic v2 schemas with latitude/longitude and blank-field checks
- **Consistent API responses** — Standard `{ success, data }` / `{ success, message }` format
- **Error handling** — Custom handlers for 404, 422, and 500 errors
- **Logging** — Structured logging for startup, shutdown, requests, CRUD, and errors
- **Health check** — `GET /health` endpoint for monitoring
- **Auto-generated docs** — Swagger UI and ReDoc
- **Docker support** — Dockerfile and docker-compose for containerized deployment
- **SQLite database** — Addresses persisted locally (PostgreSQL supported via `DATABASE_URL`)

## Folder Structure

```
Address-Manager/
├── app/
│   ├── api/routes.py          # API endpoints
│   ├── core/                  # Config, exceptions, logging
│   ├── db/                    # SQLAlchemy engine and sessions
│   ├── models/address.py      # Database model
│   ├── schemas/address.py     # Request/response schemas
│   ├── services/              # Business logic
│   ├── utils/geo.py           # Haversine distance calculation
│   └── main.py                # FastAPI application entry point
├── tests/                     # Pytest test suite
├── requirements.txt
├── Dockerfile
└── docker-compose.yml
```

## Installation and Running Locally

### Prerequisites

- Python 3.12+
- pip

### Setup

```bash
cd Address-Manager
python -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

```bash
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API runs at `http://localhost:8000`. Database tables are created automatically on startup using SQLite (`sqlite:///./address_book.db` by default).

### API Documentation (local)

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)

## Running Tests

```bash
pytest
```

## Sample API Calls

### Health Check

```bash
curl -X GET "http://localhost:8000/health"
```

### Create Address

```bash
curl -X POST "http://localhost:8000/addresses" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Acme Corporation",
    "address_line1": "123 Main Street",
    "address_line2": "Suite 400",
    "city": "San Francisco",
    "state": "CA",
    "country": "United States",
    "postal_code": "94105",
    "latitude": 37.7749,
    "longitude": -122.4194
  }'
```

### List Addresses

```bash
curl -X GET "http://localhost:8000/addresses?page=1&page_size=10&sort_by=name&sort_order=asc"
```

### Get Single Address

```bash
curl -X GET "http://localhost:8000/addresses/{id}"
```

### Update Address

```bash
curl -X PUT "http://localhost:8000/addresses/{id}" \
  -H "Content-Type: application/json" \
  -d '{"name": "Acme Corp HQ", "city": "Oakland"}'
```

### Delete Address

```bash
curl -X DELETE "http://localhost:8000/addresses/{id}"
```

### Search Nearby Addresses

```bash
curl -X GET "http://localhost:8000/addresses/nearby?latitude=37.7749&longitude=-122.4194&distance_km=10"
```

## Running with Docker

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed
- Docker Compose (included with Docker Desktop)

Uses SQLite with a persistent volume so data survives container restarts.

**1. Clone the repository and open the project folder:**

```bash
cd Address-Manager
```

**2. Build and start the API:**

```bash
docker compose up --build
```

**3. Verify the API is running:**

- Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
- Health check: [http://localhost:8000/health](http://localhost:8000/health)

```bash
curl http://localhost:8000/health
```

**4. Stop the container:**

Press `Ctrl+C`, then:

```bash
docker compose down
```

To stop and remove the database volume (deletes all saved addresses):

```bash
docker compose down -v
```

The SQLite database file is stored at `/app/data/address_book.db` inside the container, backed by the `address_book_data` Docker volume.

## Design Decisions

1. **Layered architecture** — Routes delegate to `AddressService`, which uses an embedded `AddressRepository` for clear separation of concerns (HTTP → Service → Repository → Database).

2. **Synchronous SQLAlchemy** — SQLite works well with sync sessions; this keeps the stack simple while still using FastAPI dependency injection.

3. **Haversine in Python** — Proximity search loads addresses and filters in-memory. Suitable for moderate datasets; a bounding-box pre-filter or spatial index would be a natural upgrade for large datasets.

4. **Consistent response envelope** — All endpoints return `{ success, data }` or `{ success, message }` for predictable client integration.

5. **Route ordering** — `/addresses/nearby` is registered before `/addresses/{id}` to prevent path parameter conflicts.

6. **Pydantic v2 validation** — Field validators strip whitespace and reject blank required strings; coordinate bounds are enforced at both schema and query parameter levels.

7. **Environment-driven config** — `pydantic-settings` loads configuration from environment variables with sensible defaults for local development.
