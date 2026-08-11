from typing import Final, Optional
import uuid
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import Depends, FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from numpy._core.numerictypes import int16
from redis.client import PubSub
from sqlmodel import Session, create_engine, SQLModel
from anyio import to_thread
import asyncio
import redis.asyncio as aioredis


from app.config import (
    settings, 
    DEFAULT_FRACTAL_CX, 
    DEFAULT_FRACTAL_CY, 
    DEFAULT_FRACTAL_ITERATIONS, 
    DEFAULT_FRACTAL_ZOOM
)
from app.models import ComputeJob, GraphJob, JobStatus, FractalRequest
from app.worker import run_complex_computation, generate_fractal_graph


# MySQL connections can drop if idle, so we add a pool_recycle time
engine = create_engine(
    settings.DATABASE_URL, 
    pool_recycle=3600, 
    echo=(settings.ENVIRONMENT == "development")
)


@asynccontextmanager # decorates into "async with"
async def lifespan(app: FastAPI):
    # "async def" don’t run immediately when called; 
    # they return a coroutine object
    await to_thread.run_sync(SQLModel.metadata.create_all, engine)
    # to run synchronous code in an asynchronous context
    # to_thread.run_sync is used
    # but we put the synchronous code to other thread, so we still need "await" for it
    ############################################################
    # before starting the app part before the "yield" statement are executed
    yield
    # after the app is stopped part after the "yield" statement are executed

app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)


def get_db() -> Session:
    with Session(engine) as session:
        # "with" statement ensures the resource (session) is closed 
        # after the block is executed
        yield session # pause to not cleanup the session yet


static_dir = Path(__file__).parent / "static"
index_html = (static_dir / "index.html").read_text()


@app.get("/", response_class=HTMLResponse, include_in_schema=False)
# executes "get", returns decorator that wraps the function
def frontend():
    return index_html


@app.post("/compute", status_code=202)
def dispatch_computation(payload: dict, db: Session = Depends(get_db)):
    # Depends(get_db) is a dependency injection
    """Receives request, spins up background task, and returns immediate tracking ID."""
    complexity = payload.get("complexity", 10)
    job_id = str(uuid.uuid4())

    # Register job tracker in database
    new_job = ComputeJob(id=job_id, input_data=complexity)
    print(new_job)
    db.add(new_job)
    db.commit()

    # .delay() dispatches the task over to Redis/Celery immediately
    # Does not wait
    run_complex_computation.delay(job_id, complexity)

    return {"job_id": job_id, "status": "PENDING", "message": "Calculation started in background"}


@app.get("/compute/{job_id}")
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    """Allows client to poll status or fetch finalized results."""
    job = db.get(ComputeJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job


@app.post(
    "/fractal",
    status_code=202,
    tags=["Mathematical Computations"], # for OpenAPI documentation
)
def compute_math_graph(payload: FractalRequest,  db: Session = Depends(get_db)):
    # FractalRequest is a DTO
    job_id = str(uuid.uuid4())
    new_job = GraphJob( # GraphJob is an Entity
        id=job_id,
        center_x=payload.cx or DEFAULT_FRACTAL_CX,
        center_y=payload.cy or DEFAULT_FRACTAL_CY,
        zoom=payload.zoom or DEFAULT_FRACTAL_ZOOM,
        max_iterations=payload.iterations or DEFAULT_FRACTAL_ITERATIONS
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


@app.get(
    "/fractal/{job_id}/graph",
    # Explicitly state the primary successful response media type
    response_class=Response,
    responses={
        200: {
            "content": {"image/png": {}},
            "description": "The compiled mathematical fractal plot graph returned as a raw binary PNG stream.",
        },
        202: {
            "description": "The math engine is still computing the matrix. Returns processing metadata status.",
            "content": {"application/json": {}},
        },
        404: {
            "description": "The requested mathematical job ID does not exist in the persistence layer."
        },
    },
    description="Extracts the raw binary mathematical graph from MySQL storage and streams it directly to the client asset pool.",
    tags=["Mathematical Computations"],
)
def get_computed_graph(job_id: str, db: Session = Depends(get_db)):
    job = db.get(GraphJob, job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Math job {job_id} not found")
    match job.status:
        case JobStatus.RUNNING:
            return Response(
                content=f'{{"job_id": "{job_id}", "status": "{job.status}", "message": "Graph is still compiling"}}', 
                status_code=202,
                media_type="application/json"
            )        
        case JobStatus.FAILED:
            return Response(
                content=f'{{"job_id": "{job_id}", "status": "{job.status}", "message": "Graph processing failed"}}',
                status_code=400,
                media_type="aplication/json"
            )

    # Return raw binary bytes directly as a media stream response object
    return Response(content=job.generated_graph, media_type="image/png")


@app.websocket("/fractal/{job_id}/stream")
async def stream_job_status(job_id: str, websocket: WebSocket):
    # Accept the incoming persistent TCP handshake
    await websocket.accept()
    # Establish an asynchronous connection to the Redis queue
    async_redis = aioredis.from_url(settings.REDIS_URL)
    pubsub: PubSub = async_redis.pubsub()

    channel_name = f"job_status:{job_id}" # it should've been a constant ofc
    await pubsub.subscribe(channel_name)
    try:
        # Send an immediate connection acknowledgment back to the client
        await websocket.send_json({"status": "CONNECTED", "message": f"Listening for changes on job {job_id}"})

        # Enter an async listening loop
        while True:
            # Look for a message on the Redis channel without blocking other API routes
            message: Optional[str] = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)

            if message:
                # Extract the payload bytes out of the Redis frame data
                data_signal = message['data'].decode('utf-8')

                if data_signal == JobStatus.COMPLETED.value:
                    # Fire the event down to the client
                    await websocket.send_json({
                        "status": "SUCCESS", 
                        "message": "Mathematical rendering engine finished processing.",
                        "graph_url": f"/fractal/{job_id}/graph"
                    })
                    break # while
            # extra pause after each poll
            await asyncio.sleep(0.1)
    
    except WebSocketDisconnect:
        print(f"Client disconnected early from streaming socket for job: {job_id}")
    finally:
        # Production Clean-up: Always unsubscribe and close sockets to prevent file descriptor leaks
        await pubsub.unsubscribe(channel_name)
        await websocket.close()
        

