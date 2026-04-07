# AgeOverflow Analysis Service

## Project Overview

This project is a **FastAPI-based multi-modal photo analysis service** that integrates the **AgeOverflow Engine** to estimate the age and generational distribution of user-submitted photos. The system supports asynchronous request processing, persistent storage, and REST API access for querying results and statistics.

Key features:

- SQLite for persistent storage
- Docker container support
- FastAPI REST API aligned with assignment specifications
- Swagger UI `/docs` for testing APIs
- Background processing of requests with asynchronous worker

---

## Directory Structure

```
cloud_app/
├─ app/
│  ├─ main.py           # FastAPI application entrypoint
│  ├─ models.py         # SQLAlchemy data models
│  ├─ schemas.py        # Pydantic schemas
│  ├─ routers/
│  │  └─ analysis.py    # API routes
│  └─ worker.py         # Background task processing
├─ Dockerfile
├─ local.sh             # Startup script
├─ requirements.txt
├─ ageoverflow.db       # SQLite database (generated on first run)
└─ sample_input.json    # Engine test sample
```

---

## Environment Requirements

- Python 3.12
- FastAPI
- SQLAlchemy
- SQLite (Python built-in)
- Docker (optional for containerized deployment)
- AgeOverflow Engine (integrated in Docker image)

Install Python dependencies:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

---

## Running Locally (Without Docker)

1. Activate the virtual environment:

```bash
source venv/bin/activate
```

2. Start the FastAPI service:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

3. Open Swagger UI:

```
http://localhost:8080/docs
```

Use it to test all API endpoints.

---

## Running with Docker (Recommended)

1. Build Docker image:

```bash
docker build -t ageoverflow .
```

2. Run container:

```bash
docker run --rm -p 8080:8080 ageoverflow
```

3. Access API:

```
http://localhost:8080/docs
```

4. Export Docker image (optional):

```bash
docker save -o ageoverflow.tar ageoverflow:latest
```

5. Import on another machine:

```bash
docker load -i ageoverflow.tar
docker run --rm -p 8080:8080 ageoverflow
```

---

## API Overview

All endpoints are prefixed with `/api/v1/analysis`.

### 1. Submit Analysis Request

```http
POST /{customer_id}/requests
```

**Request body:**

```json
{
  "user_id": "UUID",
  "urgent": false,
  "photos": ["base64_photo_1", "base64_photo_2"]
}
```

**Response:** `RequestDetailResponse`  
- Returns `status=pending`
- Background task processes the request asynchronously

---

### 2. List Analysis Requests

```http
GET /{customer_id}/requests
```

- Returns `list[RequestSummaryResponse]`
- Query parameters:
  - `limit` / `offset`
  - `start` / `end`
  - `user_id`
  - `status` (`pending` / `success` / `failed`)
  - `generation`

---

### 3. Get Single Request Detail

```http
GET /{customer_id}/requests/{request_id}
```

- Returns `RequestDetailResponse`
- Includes:
  - `photos`
  - `probabilities`
  - `estimated_age_low` / `estimated_age_high`
  - `error_message`
  - `engine_version`

---

### 4. Users List & Detail

```http
GET /{customer_id}/users
GET /{customer_id}/users/{user_id}
```

- Returns user info and their requests
- `UserDetailResponse` includes request summaries

---

### 5. Statistics

```http
GET /{customer_id}/statistics
```

- Returns `StatisticsResponse`
- Includes:
  - Total requests
  - Pending / Success / Failed
  - Urgent requests
  - Generation distribution

---

### 6. Health Check

```http
GET /health
```

- Returns `HealthResponse`
- Checks service and database status

