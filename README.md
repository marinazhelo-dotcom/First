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

### 4. Advanced Production Orchestration
* **The Paradigm:** Treating architecture as code and establishing iron-clad security boundaries between services.
* **The Practice:** * Writing production-grade **Dockerfiles** that ditch `root` access to run as a secure, unprivileged `appuser`.
  * Implementing **Docker Compose Healthchecks** to handle container race conditions and service boot sequencing smoothly.
  * Mastering Python 3.10+ **Structural Pattern Matching (`match/case`)** to cleanly route complex data payloads without dirty `if/else` nests.

---

## 🏗️ System Architecture

The application separates concerns into independent, highly scalable infrastructure layers:
* **API Gateway (`FastAPI`)**: Ingests incoming parameters, handles validation, creates transaction logs, and pushes lightweight job tokens to the message broker.
* **Message Broker (`Redis`)**: Manages the high-throughput asynchronous task queue.
* **Compute Engine (`Celery`)**: Headless background workers optimized for CPU-heavy mathematical computations (Mandelbrot vector matrices).
* **Storage Layer (`MySQL`)**: Persists job statuses and archives generated graph plots as raw binary blobs (`LONGBLOB`).

---

## 🚀 Quick Start (Docker Orchestration)

The fastest way to spin up the complete production-ready cluster (including database provisions and internal network bridges) is via Docker Compose.

### 1. Prerequisites
Ensure you have the following systems installed natively on your host machine:
* Docker (v20.10+)
* Docker Compose (v2.0+)

### 2. Launch the Cluster
Execute the orchestrated build command:

```Bash
docker compose up --build
```

Note: The system utilizes explicit Docker Compose Healthchecks. The API gateway and Celery workers will wait in a holding pattern until the MySQL storage engine finishes initializing and passes its network verification loops.

---

## 📡 Core API Specifications

Once the API gateway initializes, open your browser and access the interactive Swagger Documentation portal at: ```http://0.0.0.0:8000/docs```
### 1. Dispatch a Compute Job
Endpoint: ```POST /fractal```
Payload Format:
```json
{
  "cx": -0.7,
  "cy": 0.27015,
  "zoom": 1.5,
  "iterations": 150
}
```
