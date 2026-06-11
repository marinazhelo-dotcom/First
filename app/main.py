import uuid
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Response
from sqlmodel import Session, create_engine, SQLModel
from anyio import to_thread

from app.config import settings
from app.models import ComputeJob, GraphJob, JobStatus
from app.worker import run_complex_computation, generate_fractal_graph


# MySQL connections can drop if idle, so we add a pool_recycle time
engine = create_engine(
    settings.DATABASE_URL, 
    pool_recycle=3600, 
    echo=(settings.ENVIRONMENT == "development")
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await to_thread.run_sync(SQLModel.metadata.create_all, engine)
    yield

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


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


@app.post("/fractal", status_code=202)
def compute_math_graph(payload: dict,  db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())
    new_job = GraphJob(
        id=job_id,
        center_x=payload.get("cx", -0.7),
        center_y=payload.get("cy", 0.27015),
        zoom=payload.get("zoom", 1.0),
        max_iterations=payload.get("iterations", 100)
    )
    db.add(new_job)
    db.commit()

    generate_fractal_graph.delay(
        job_id=new_job.id,
        cx=new_job.center_x, # take from db?
        cy=new_job.center_y,
        zoom=new_job.zoom,
        max_iter=new_job.max_iterations
    )
    return {"job_id": job_id, "status": "PENDING"}

@app.get("/fractal/{job_id}/graph")
def get_computed_graph(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GraphJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Math job {job_id} not found")
    match job.status:
        case JobStatus.RUNNING:
            return {"job_id": job_id, "status": job.status, "message": "Graph is still compiling"}
        case JobStatus.FAILED:
            return {"job_id": job_id, "status": job.status, "message": "Graph processing failed"}

    # Return raw binary bytes directly as a media stream response object!
    return Response(content=job.generated_graph, media_type="image/png")
