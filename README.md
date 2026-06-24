# 🚀 Distributed Math Engine (Educational Testing Grounds)

This is a sandbox testing project built explicitly to practice and master high-performance, asynchronous Python architectures. The primary objective of this codebase is to learn how to transition from traditional synchronous web applications to a distributed, event-driven system capable of handling heavy data science, mathematical modeling, and background asset compilation.

---

## 🎯 Core Learning Objectives & Skills Mastered

By working through this testing project, you are actively learning and practicing several advanced backend engineering paradigms:

### 1. Asynchronous Systems & Task Queuing
* **The Paradigm:** Moving heavy, blocking compute blocks out of the HTTP request-response lifecycle.
* **The Practice:** Learning how FastAPI immediately responds with a `202 Accepted` token while handing heavy CPU loops off to **Celery** and **Redis** to protect API throughput.

### 2. High-Performance Vectorized Mathematics
* **The Paradigm:** Bypassing slow, single-threaded vanilla Python `for` loops in computational mathematics.
* **The Practice:** Utilizing **NumPy** to build and calculate multi-dimensional coordinate grids simultaneously, learning the mechanics of `@array_function_dispatch` and native C-extensions (`greenlet`).

### 3. Headless Asset Compilation & Binary Blobs
* **The Paradigm:** Generating structural visual data inside an isolated server environment without a monitor or GUI interface.
* **The Practice:** Configuring **Matplotlib** to run on the memory-only `Agg` backend, capturing the output as an in-memory byte stream, and practicing serialization by saving raw PNG bytes into a MySQL `LONGBLOB` database layer.

### 4. Real-Time Event Streaming
* **The Paradigm:** Replacing inefficient polling loops with push-based notifications when long-running jobs finish.
* **The Practice:** Publishing job completion events from Celery workers via **Redis Pub/Sub**, and consuming them over a persistent **WebSocket** connection so clients receive instant status updates without hammering the REST API.

### 5. Advanced Production Orchestration
* **The Paradigm:** Treating architecture as code and establishing iron-clad security boundaries between services.
* **The Practice:**
  * Writing production-grade **Dockerfiles** that ditch `root` access to run as a secure, unprivileged `appuser`.
  * Implementing **Docker Compose Healthchecks** to handle container race conditions and service boot sequencing smoothly.
  * Mastering Python 3.10+ **Structural Pattern Matching (`match/case`)** to cleanly route complex data payloads without dirty `if/else` nests.
  * Managing schema evolution with **Alembic** migrations (including `LONGBLOB` upgrades for graph storage).

---

## 🏗️ System Architecture

The application separates concerns into independent, highly scalable infrastructure layers:

* **API Gateway (`FastAPI`)**: Ingests incoming parameters, handles validation, creates transaction logs, pushes lightweight job tokens to the message broker, and exposes WebSocket endpoints for live status streaming.
* **Message Broker (`Redis`)**: Manages the high-throughput asynchronous Celery task queue **and** Pub/Sub channels for real-time job completion events (`job_status:{job_id}`).
* **Compute Engine (`Celery`)**: Headless background workers optimized for CPU-heavy mathematical computations (Mandelbrot vector matrices and simulated compute loops).
* **Storage Layer (`MySQL`)**: Persists job statuses and archives generated graph plots as raw binary blobs (`LONGBLOB`).

```
Client ──POST /fractal──▶ FastAPI ──.delay()──▶ Redis (Celery queue)
                              │                        │
                              │                        ▼
                              │                   Celery Worker
                              │                        │
                              │              publish COMPLETED
                              │                        │
                              ▼                        ▼
                           MySQL ◀──── save PNG ── Redis Pub/Sub
                              ▲
Client ◀── WebSocket stream ──┘ (instant notification)
Client ◀── GET /fractal/{id}/graph ── (fetch PNG)
```

---

## 🚀 Quick Start (Docker Orchestration)

The fastest way to spin up the complete production-ready cluster (including database provisions and internal network bridges) is via Docker Compose.

### 1. Prerequisites

Ensure you have the following systems installed natively on your host machine:

* Docker (v20.10+)
* Docker Compose (v2.0+)

### 2. Launch the Cluster

Execute the orchestrated build command:

```bash
docker compose up --build
```

Note: The system utilizes explicit Docker Compose Healthchecks. The API gateway and Celery workers will wait in a holding pattern until the MySQL storage engine finishes initializing and passes its network verification loops.

### 3. Services & Ports

| Service        | Container         | Port  |
|----------------|-------------------|-------|
| FastAPI API    | `compute_fastapi` | 8000  |
| Celery Worker  | `compute_celery`  | —     |
| MySQL          | `compute_mysql`   | 3307  |
| Redis          | `compute_redis`   | 6379  |

---

## 📡 Core API Specifications

Once the API gateway initializes, open the interactive Swagger documentation at:

**http://0.0.0.0:8000/docs**

### Compute Jobs

#### `POST /compute`

Dispatches a generic CPU-bound computation task. Returns immediately with a tracking ID.

**Payload:**

```json
{
  "complexity": 10
}
```

**Response (`202 Accepted`):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING",
  "message": "Calculation started in background"
}
```

#### `GET /compute/{job_id}`

Polls the status and result of a compute job.

**Response:** Full `ComputeJob` record (`PENDING` → `RUNNING` → `COMPLETED`).

---

### Fractal Graph Jobs

#### `POST /fractal`

Dispatches a Mandelbrot fractal rendering job. All fields are optional and fall back to defaults defined in `app/config.py`.

**Payload:**

```json
{
  "cx": -0.7,
  "cy": 0.27015,
  "zoom": 1.5,
  "iterations": 150
}
```

| Field        | Default   | Description                              |
|--------------|-----------|------------------------------------------|
| `cx`         | `-0.7`    | Real component of the complex plane center |
| `cy`         | `0.27015` | Imaginary component of the center        |
| `zoom`       | `1.0`     | Magnification factor                     |
| `iterations` | `100`     | Max escape-velocity loop iterations      |

**Response (`202 Accepted`):**

```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "PENDING"
}
```

#### `GET /fractal/{job_id}/graph`

Retrieves the rendered PNG graph once the job completes.

| Status | Meaning |
|--------|---------|
| `200`  | Returns raw `image/png` binary stream |
| `202`  | Job still running — JSON status payload |
| `400`  | Job failed during rendering |
| `404`  | Job ID not found |

See `get_fractal_response.jpeg` in the repo root for an example output image.

#### `WS /fractal/{job_id}/stream`

Opens a persistent WebSocket connection that listens on a Redis Pub/Sub channel for the given job. When the Celery worker finishes rendering, the client receives an instant push notification instead of polling.

**On connect:**

```json
{
  "status": "CONNECTED",
  "message": "Listening for changes on job {job_id}"
}
```

**On completion:**

```json
{
  "status": "SUCCESS",
  "message": "Mathematical rendering engine finished processing.",
  "graph_url": "/fractal/{job_id}/graph"
}
```

**Example with `websocat`:**

```bash
websocat ws://localhost:8000/fractal/{job_id}/stream
```

---

## 🔄 End-to-End Fractal Workflow

1. **Dispatch** — `POST /fractal` with optional center/zoom parameters.
2. **Subscribe** — Connect to `WS /fractal/{job_id}/stream` (or poll `GET /fractal/{job_id}/graph`).
3. **Wait** — Celery worker renders the Mandelbrot set with NumPy + Matplotlib and stores the PNG in MySQL.
4. **Notify** — Worker publishes `COMPLETED` to Redis; WebSocket client receives the `graph_url`.
5. **Fetch** — `GET /fractal/{job_id}/graph` returns the binary PNG.

---

## 🗄️ Database Migrations (Alembic)

Schema changes are managed with Alembic. The `GraphJob.generated_graph` column uses `LONGBLOB` to store full-resolution PNG payloads.

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "describe your change"

# Apply pending migrations
alembic upgrade head
```

Migration scripts live in `alembic/versions/`.

---

## 📦 Key Dependencies

| Package              | Role                                      |
|----------------------|-------------------------------------------|
| `fastapi` / `uvicorn`| Async HTTP API gateway                    |
| `celery` / `redis`   | Task queue broker and Pub/Sub             |
| `sqlmodel` / `pymysql` | ORM and MySQL driver                    |
| `numpy` / `matplotlib` | Vectorized math and headless plotting |
| `websockets`         | WebSocket protocol support                |
| `redis[hiredis]`     | High-performance Redis client             |
| `alembic`            | Database schema migrations                |

---

## 🛠️ Local Development (without Docker)

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set environment variables (or create a .env file)
export DATABASE_URL="mysql+pymysql://user:pass@localhost:3307/compute_api_db"
export REDIS_URL="redis://localhost:6379/0"
export ENVIRONMENT="development"
export APP_NAME="High-Performance Compute API"
export SECRET_KEY="your-secret-key"

# Terminal 1 — API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Terminal 2 — Celery worker
celery -A app.worker.celery_app worker --loglevel=info
```

MySQL and Redis must be running locally (or via `docker compose up mysql_db redis_queue`).
