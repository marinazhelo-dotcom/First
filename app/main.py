import uuid
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException
from fastapi.dependencies.models import Dependant
from sqlmodel import Session, create_engine, SQLModel
from anyio import to_thread

from app.config import settings
from app.models import ComputeJob
from app.worker import run_complex_computation

# MySQL connections can drop if idle, so we add a pool_recycle time
engine = create_engine(settings.DATABASE_URL, pool_recycle=3600, echo=(settings.ENVIRONMENT == "development"))
app = FastAPI(title=settings.APP_NAME)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await to_thread.run_sync(SQLModel.metadata.create_all, engine)
    yield

def get_db() -> Session:
    with Session(engine) as session:
        yield session

@app.post("/compute", status_code=202)
def dispatch_computation(payload: dict, db: Session = Depends(get_db)):
    """Receives request, spins up background task, and returns immediate tracking ID."""
    complexity = payload.get("complexity", 10)
    job_id = str(uuid.uuid4())

    # Register job tracker in database
    new_job = ComputeJob(id=job_id, input_data=complexity)
    print(new_job)
    print(ComputeJob())
    db.add(new_job)
    db.commit()
    
    # .delay() dispatches the task over to Redis/Celery immediately!
    # The API code execution path passes over this instantly in microseconds.
    run_complex_computation.delay(job_id, complexity)

    return {"job_id": job_id, "status": "PENDING", "message": "Calculation started in background"}
    
@app.get("/compute/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Allows client to poll status or fetch finalized results."""
    job = db.get(ComputeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job

