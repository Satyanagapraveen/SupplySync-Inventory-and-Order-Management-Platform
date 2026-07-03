
## SupplySync: Enterprise Inventory & Order Management API

SupplySync is a robust, highly scalable backend built to manage complex warehouse operations, inventory tracking, and order lifecycles.

Unlike simple CRUD applications, SupplySync is built around strict business logic. It enforces segregation of duties, prevents race conditions during high-volume inventory transfers, and offloads heavy processing to background workers. This API acts as the central brain for web dashboards and mobile applications used by warehouse staff, procurement managers, and administrators.

## Project Structure

```text
supplysync/ (project settings directory)
settings/
    __init__.py
    base.py
    development.py
    production.py
    testing.py
__init__.py
celery.py
asgi.py    
urls.py
wsgi.py

apps/
    accounts/ (user management and authentication)
    warehouses/ (warehouse management)
    categories/ (product category management)
    products/ (product management)
    inventory/ (inventory tracking and transactions)
    suppliers/ (supplier management)
    purchase_orders/ (purchase order lifecycle)
    sales_orders/ (sales order lifecycle)
    reports/ (analytics and reporting)

core/ (shared utilities, base classes, helpers)
    apps.py
    models.py
    serializers.py
    permissions.py
    pagination.py
    exceptions.py
    utils.py
    constants.py
    tasks.py
tests/ (unit and integration tests)
        conftest.py
        test_accounts/
        test_inventory/
        test_purchase_orders/
        test_sales_orders/
```

## Technology Stack

- Python 3.11 or 3.12
- Django 5.x
- Django REST Framework 3.15.x
- PostgreSQL (primary relational database)
- Redis (caching and Celery broker)
- Celery with Redis as broker (background tasks and event streaming equivalent)
- Celery Beat (periodic and scheduled tasks)
- Simple JWT (djangorestframework-simplejwt) for authentication
- Django Filters (django-filter) for dynamic filtering
- drf-spectacular (OpenAPI documentation)
- Pytest and pytest-django (testing)
- Docker and Docker Compose

## 🏗 System Architecture

The system is designed with a clear separation of concerns, utilizing an API gateway, background task processing, and a dedicated caching/broker layer.

```mermaid
graph TD
    subgraph Client Layer
        Client[Web Dashboard / Mobile App]
    end

    subgraph API Gateway & Application
        Django[Django REST API <br/> Gunicorn/WSGI]
    end

    subgraph Background Processing
        Worker[Celery Worker <br/> Event Processing]
        Beat[Celery Beat <br/> Cron Jobs]
    end

    subgraph Data & Caching Layer
        DB[(PostgreSQL 15 <br/> supplysync_db)]
        Redis[(Redis 7 <br/> Cache & Broker)]
    end

    Client -- "HTTP REST Calls" --> Django
    Django -- "Reads/Writes Data" --> DB
    Django -- "Caches Data / Queues Tasks" --> Redis
    Beat -- "Schedules Tasks" --> Redis
    Worker -- "Consumes Tasks" --> Redis
    Worker -- "Reads/Writes Data" --> DB

    classDef layer fill:#f9f9f9,stroke:#ccc,stroke-width:1px;
    class Client,Django,Worker,Beat,DB,Redis layer;
```

## 🧠 Core Engineering Concepts

I didn't just build features; I built them using enterprise-grade patterns:

**Service Layer Architecture:** Business logic (math, inventory validation, state transitions) is entirely stripped out of `views.py` and `serializers.py`. Views handle HTTP, Serializers handle validation, and `services.py` acts as the brain. This makes the code highly reusable and easily testable.

**Concurrency & Data Integrity:** I use `@transaction.atomic` and `select_for_update()` row-level database locking to prevent race conditions. If two managers try to reserve the last laptop at the exact same millisecond, the database handles it safely.

**Role-Based Access Control (RBAC) & JWT:** Security is granular. A Warehouse Worker can adjust inventory, but only a Procurement Manager can approve a Purchase Order. Auth is handled via stateless JSON Web Tokens.

**Redis-Backed Rate Limiting:** The authentication endpoints are protected against brute-force attacks using a custom hybrid throttle. I track failed login attempts in Redis (5 fails / 15 minutes) and lock the user out dynamically.

**Asynchronous Processing (Celery):** Heavy tasks (like generating PDF reports, sending low-stock emails, or complex data aggregation) are passed to a Redis message broker and processed in the background by Celery workers, keeping API response times under 100ms.

**Test-Driven Reliability:** The system includes a comprehensive suite of Unit and Integration tests (via pytest) covering happy paths, edge cases, custom DRF exceptions, and permission blocks.

## 🧗 The Journey: Challenges & Resolutions

Building this wasn't without its hurdles. Here are a few notable challenges I encountered and conquered:

**The "Data Contract" Mismatch:**
- **Problem:** Early integration tests failed because the View layer was passing IDs (e.g., `warehouse_id`) but the Service layer explicitly expected object instances (e.g., `warehouse`).
- **Fix:** I aligned the data contracts. Services were updated to safely use `.get('key_id')` and fall back gracefully, ensuring seamless communication between API serializers and internal functions.

**DRF Exception Handling Quirks:**
- **Problem:** When testing dynamic error codes (like `INVALID_STATUS_TRANSITION`), standard exception testing failed because Django REST Framework buries custom codes inside its response objects.
- **Fix:** I dove into DRF internals and switched my test assertions to use `exc_info.value.get_codes()`, allowing me to perfectly validate the API's error responses.

**The Docker "Localhost" Trap:**
- **Problem:** When moving from a local environment to Docker Compose, Celery workers crashed with `Connection refused`. They were looking for Postgres and Redis at `localhost`, which inside a container just points to the container itself.
- **Fix:** I remapped my `settings.py` to use Docker's internal DNS (e.g., `DB_HOST=postgres`, `CELERY_BROKER_URL=redis://redis:6379/0`), successfully linking the container fleet.

## 🚀 Getting Started (Setup)

The entire infrastructure is containerized. You do not need to install Postgres or Redis on your local machine.

1. **Spin up the Infrastructure**

   This command builds the container images and starts the Postgres, Redis, and Celery services in the background.

   ```bash
   docker-compose up -d --build
   ```

2. **Run Database Migrations**

   ```bash
   python manage.py migrate
   ```

3. **Create an Admin User**

   ```bash
   python manage.py createsuperuser
   ```

4. **Run the Local Development Server**

   ```bash
   python manage.py runserver
   ```

   The API is now accessible at http://127.0.0.1:8000. You can view the interactive Swagger documentation at `/api/schema/swagger-ui/`.

## 📡 API Reference & Endpoints

All endpoints support pagination where applicable.

### 🔐 Authentication (`/api/v1/auth/`)
- `POST /login/` - Authenticate and receive JWT pair.
- `POST /register/` - Register a new system user.
- `POST /token/refresh/` - Refresh an expired access token.
- `POST /logout/` - Blacklist the current token.
- `PUT /change-password/` - Update user credentials.

### 📦 Inventory & Warehouses
- `GET /warehouses/ | POST | GET {id} | PUT {id} | PATCH {id} | DELETE {id}`
- `GET /categories/ | POST | GET /tree/` (Returns recursive category hierarchy)
- `GET /products/ | POST | GET {id} | PUT {id} | PATCH {id} | DELETE {id}`
- `POST /inventory/adjust/` - Manually adjust stock levels.
- `POST /inventory/transfer/` - Move stock between warehouses safely.
- `GET /inventory/low-stock/` - Returns cached list of items below reorder thresholds.
- `GET /inventory/warehouse/{warehouse_id}/`

### 🛒 Purchase Orders (Inbound)
- `GET /purchase-orders/ | POST`
- `POST /purchase-orders/{id}/submit/` - Move from Draft to Pending.
- `POST /purchase-orders/{id}/approve/` - Manager approval (blocks self-approval).
- `POST /purchase-orders/{id}/receive/` - Intake stock and update inventory automatically.
- `POST /purchase-orders/{id}/cancel/`

### 🚚 Sales Orders (Outbound)
- `GET /sales-orders/ | POST` (Reserves inventory instantly)
- `POST /sales-orders/{id}/dispatch/` - Deducts reserved inventory and generates outbound transactions.
- `POST /sales-orders/{id}/deliver/`
- `POST /sales-orders/{id}/cancel/` - Releases reserved inventory back to available pool.

### 🏢 Suppliers & Reports
- `GET /suppliers/ | POST | GET {id} | PUT {id} | PATCH {id} | DELETE {id}`
- `GET /reports/dashboard/` - High-level system metrics.
- `GET /reports/inventory-valuation/` - Financial stock evaluation.
- `GET /reports/purchase-orders/summary/`
- `GET /reports/sales-orders/summary/`

## 💻 Example cURL Commands for Testing

### 1. Login to get a JWT Token

```bash
curl -X POST http://127.0.0.1:8000/api/v1/auth/login/ \
-H "Content-Type: application/json" \
-d '{"email": "admin@test.com", "password": "TestPassword123!"}'
```

Copy the `access_token` from the response for the next requests.

### 2. Create a Sales Order (Requires JWT)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/sales-orders/ \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
-H "Content-Type: application/json" \
-d '{
  "customer_name": "Acme Corp",
  "customer_email": "purchasing@acme.com",
  "warehouse_id": 1,
  "items": [
    {
      "product_id": 42,
      "quantity": 10,
      "unit_price": "999.99"
    }
  ]
}'
```

### 3. Transfer Inventory (Requires JWT)

```bash
curl -X POST http://127.0.0.1:8000/api/v1/inventory/transfer/ \
-H "Authorization: Bearer YOUR_ACCESS_TOKEN_HERE" \
-H "Content-Type: application/json" \
-d '{
  "product_id": 42,
  "source_warehouse_id": 1,
  "destination_warehouse_id": 2,
  "quantity": 50,
  "notes": "Rebalancing regional stock."
}'
```

You can also send requests through the interactive documentation:

http://localhost:8000/api/schema/swagger-ui/#/
