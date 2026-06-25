# Address Book REST API

A production-quality FastAPI application for managing addresses with full CRUD operations, proximity search using the Haversine formula, pagination, filtering, and comprehensive validation.

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
- **Code quality** — Black, Ruff, isort, and pre-commit hooks

## Folder Structure

```
address-book-api/
├── app/
│   ├── api/
│   │   └── routes.py          # API endpoints and dependency injection
│   ├── core/
│   │   ├── config.py          # Environment-based settings
│   │   ├── exceptions.py      # Custom application exceptions
│   │   └── logging.py         # Logging configuration
│   ├── db/
│   │   ├── database.py        # SQLAlchemy engine and Base
│   │   └── session.py         # Session factory and get_db dependency
│   ├── models/
│   │   └── address.py         # SQLAlchemy Address model
│   ├── schemas/
│   │   └── address.py         # Pydantic request/response schemas
│   ├── services/
│   │   └── address_service.py # Repository + service business logic
│   ├── utils/
│   │   └── geo.py             # Haversine distance calculation
│   └── main.py                # FastAPI app, middleware, exception handlers
├── tests/
│   ├── conftest.py            # Shared pytest fixtures
│   ├── test_create.py
│   ├── test_update.py
│   ├── test_delete.py
│   ├── test_nearby.py
│   └── test_validation.py
├── .env.example
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── docker-compose.yml
├── .pre-commit-config.yaml
└── README.md
```

## Installation

### Prerequisites

- Python 3.12 or 3.13 (recommended; Python 3.14 may lack pre-built wheels for some dependencies)
- pip

### Virtual Environment Setup

```bash
cd address-book-api
python -m venv .venv
```

On Windows, if `python` resolves to 3.14, use an explicit 3.12+ interpreter:

```powershell
py -3.13 -m venv .venv
```

**Windows (PowerShell):**

```powershell
.\.venv\Scripts\Activate.ps1
```

**macOS / Linux:**

```bash
source .venv/bin/activate
```

### Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Environment Variables

Copy the example environment file and adjust as needed:

```bash
cp .env.example .env
```

| Variable           | Default                      | Description                    |
|--------------------|------------------------------|--------------------------------|
| `APP_NAME`         | Address Book API             | Application display name       |
| `APP_VERSION`      | 1.0.0                        | Application version            |
| `DEBUG`            | false                        | Enable SQLAlchemy query echo   |
| `DATABASE_URL`     | sqlite:///./address_book.db  | SQLite connection string       |
| `LOG_LEVEL`        | INFO                         | Logging level                  |
| `DEFAULT_PAGE_SIZE`| 10                           | Default pagination page size   |
| `MAX_PAGE_SIZE`    | 100                          | Maximum allowed page size      |

## Running Locally

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.

Database tables are created automatically on startup.

## Running Tests

```bash
pytest
```

With coverage report:

```bash
pytest --cov=app --cov-report=term-missing
```

Target coverage: **>90%**

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

### List Addresses (with pagination and filters)

```bash
curl -X GET "http://localhost:8000/addresses?page=1&page_size=10&sort_by=name&sort_order=asc&country=United&name=Acme"
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

## Swagger Documentation

Interactive API documentation is available at:

- **Swagger UI:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **OpenAPI JSON:** [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

## Docker

### Build and run with Docker Compose

```bash
docker compose up --build
```

### Build and run with Docker only

```bash
docker build -t address-book-api .
docker run -p 8000:8000 address-book-api
```

## Code Quality

Install pre-commit hooks:

```bash
pre-commit install
```

Run formatters and linters manually:

```bash
black app tests
isort app tests
ruff check app tests
```

## Design Decisions

1. **Layered architecture** — Routes delegate to `AddressService`, which uses an embedded `AddressRepository` for clear separation of concerns (HTTP → Service → Repository → Database).

2. **Synchronous SQLAlchemy** — SQLite works well with sync sessions; this keeps the stack simple while still using FastAPI dependency injection.

3. **Haversine in Python** — Proximity search loads addresses and filters in-memory. Suitable for moderate datasets; a bounding-box pre-filter or spatial index would be a natural upgrade for large datasets.

4. **Consistent response envelope** — All endpoints return `{ success, data }` or `{ success, message }` for predictable client integration.

5. **Route ordering** — `/addresses/nearby` is registered before `/addresses/{id}` to prevent path parameter conflicts.

6. **Pydantic v2 validation** — Field validators strip whitespace and reject blank required strings; coordinate bounds are enforced at both schema and query parameter levels.

7. **Environment-driven config** — `pydantic-settings` loads configuration from `.env` with sensible defaults for local development.

## Future Improvements

- PostgreSQL with PostGIS for production-scale geospatial queries
- Async SQLAlchemy with connection pooling
- API authentication (JWT/OAuth2)
- Rate limiting and request ID tracing
- Database migrations with Alembic
- Bounding-box pre-filter before Haversine for performance
- OpenTelemetry metrics and distributed tracing
- Kubernetes deployment manifests

## License

MIT
