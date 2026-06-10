import time
from celery import Celery
from sqlmodel import create_engine, Session
from app.models import ComputeJob, JobStatus, SQLModel
from app.config import settings

# Connect Celery to Redis broker
celery_app = Celery(
    "compute_jobs", 
    broker=settings.REDIS_URL, 
    backend=settings.REDIS_URL
)
# SQL
sqlalchemy_engine = create_engine(settings.DATABASE_URL)
# 🚀 Force the worker process to create the tables if they don't exist yet!
SQLModel.metadata.create_all(sqlalchemy_engine)


@celery_app.task()
def run_complex_computation(job_id: str, complexity: int) -> float:
    # This function runs in a completely separate worker process.
    # 1. Update status to RUNNING in database
    with Session(sqlalchemy_engine) as session:
        job = session.get(ComputeJob, job_id)
        if job:
            job.status = JobStatus.RUNNING
            session.add(job)
            session.commit()

    # 2. Simulate a heavy CPU-bound calculation (e.g., intensive matrix loops)
    print(f"Starting complex math task {job_id}...")
    total = 0.0
    for i in range(complexity * 10000):
        total = (i ** 2) * 0.01
    time.sleep(5) # Simulating extra deep system processing latency

    # 3. Update status to SUCCESS and save data
    with Session(sqlalchemy_engine) as session:
        job = session.get(ComputeJob, job_id)
        if job:
            job.status = JobStatus.COMPLETED
            session.add(job)
            session.commit()

    return total
