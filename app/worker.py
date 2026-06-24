import time
import redis
from celery import Celery
from sqlalchemy.exc import NoResultFound
from sqlmodel import create_engine, Session
from app.models import ComputeJob, GraphJob, JobStatus, SQLModel
from app.config import settings

import io
import numpy as np
import  matplotlib
matplotlib.use('Agg')
from  matplotlib.figure import Figure
from matplotlib.backends.backend_agg import FigureCanvasAgg


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
# Redis
redis_client = redis.Redis.from_url(settings.REDIS_URL)


@celery_app.task()
def run_complex_computation(job_id: str, complexity: int) -> float:
    channel_name = f"job_status:{job_id}"
    # This function runs in a completely separate worker process.
    # 1. Update status to RUNNING in database
    change_job_status(ComputeJob, job_id, JobStatus.RUNNING)
    db_commit()


    # 2. Simulate a heavy CPU-bound calculation (e.g., intensive matrix loops)
    print(f"Starting complex math task {job_id}...")
    total = 0.0
    for i in range(complexity * 10000):
        total = (i ** 2) * 0.01
    time.sleep(5) # Simulating extra deep system processing latency

    # 3. Update status to COMPLETED and save data
    change_job_status(ComputeJob, job_id, JobStatus.COMPLETED)
    db_commit()
    redis_client.publish(channel_name, "Completed")


    return total


@celery_app.task()
def generate_fractal_graph(job_id: str, cx: float, cy: float, zoom: float, max_iter: int = 100):
    channel_name = f"job_status:{job_id}"
    # job = change_job_status(GraphJob, job_id)
    with Session(sqlalchemy_engine) as session:
        job = session.get(GraphJob, job_id)
        if job:
            job.status = JobStatus.RUNNING
            session.add(job)
            session.flush()
        else:
            print(f"No job found by {job_id}")
        session.commit()

    try:
        # 1. Define resolution dimensions for our coordinate grid matrix
        h, w = 500, 500

        # 2. Construct complex plane limits based on user zoom boundaries
        x_min, x_max = cx - (1.5 / zoom), cx + (1.5 / zoom)
        y_min, y_max = cy - (1.5 / zoom), cy + (1.5 / zoom)

        # 3. Use NumPy to create multi-dimensional math grids instantly
        X = np.linspace(x_min, x_max, num=w)
        Y = np.linspace(y_min, y_max, num=h)
        C = X + Y[:, None] * 1j
        Z = np.zeros_like(C)
        M = np.zeros(C.shape, dtype=int)

        # 4. Run the Core Mathematical Equation loop
        for i in range(max_iter):
            # Mandelbrot formula: Z = Z^2 + C
            mask: bool = np.abs(Z) <= 2
            Z[mask] = Z[mask]**2 + C[mask]
            M[mask] = i
        
        # 5. Graph the data matrix using Matplotlib
        fig = Figure(figsize=(6, 6), dpi=100)
        canvas = FigureCanvasAgg(fig)
        ax = fig.add_subplot(111)
        ax.imshow(M, cmap="twilight_shifted", extent=[x_min, x_max, y_min, y_max])
        ax.axis('off') # Clean graph layout without generic plot markers

        # 6. Save graph figure directly to an in-memory byte buffer array
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', pad_inches=0)
        buf.seek(0)
        image_bytes = buf.getvalue()
        print(f"Success! Generated image payload size: {len(image_bytes)} bytes")

        # 7. Write the raw binary bytes back to our database record
        
        with Session(sqlalchemy_engine) as session:
            job = session.get(GraphJob, job_id)
            if job:
                job.generated_graph = image_bytes
                job.status = JobStatus.COMPLETED
                session.add(job)
                session.flush()
            else:
                print(f"No job found by {job_id}")
            session.commit()


    except Exception as e:  
        with Session(sqlalchemy_engine) as session:
            job = session.get(GraphJob, job_id)
            if job:
                job.status = JobStatus.FAILED
                session.add(job)
                session.flush()
            else:
                print(f"No job found by {job_id}")
            session.commit()
        print(f"Mathematical calculation crashed: {str(e)}")
    finally:
        time.sleep(5)
        db_commit()
        res = redis_client.publish(channel_name, JobStatus.COMPLETED.value)
        print(res)


def change_job_status(entity: SQLModel, job_id: str, status: JobStatus = JobStatus.RUNNING) -> SQLModel:
    with Session(sqlalchemy_engine) as session:
        job = session.get(entity, job_id)
        if job:
            job.status = status
            session.add(job)
            session.flush()
        else:
            print(f"No job found by {job_id}")
    return job

def db_commit() -> None:
    with Session(sqlalchemy_engine) as session:
        session.commit()

def db_save(job) -> None:
    with Session(sqlalchemy_engine) as session:
        session.add(job)
