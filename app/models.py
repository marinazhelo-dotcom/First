from termios import CBAUDEX
from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum
from datetime import datetime, UTC, timezone
from pydantic import BaseModel, Field as PyField

from app.config import (
    DEFAULT_FRACTAL_CX,
    DEFAULT_FRACTAL_CY, 
    DEFAULT_FRACTAL_ITERATIONS, 
    DEFAULT_FRACTAL_ZOOM
)


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


""" DB """
class ComputeJob(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=36)
    status: JobStatus = Field(default=JobStatus.PENDING, max_length=20)
    input_data: int # Say, matrix size or complexity level
    result: Optional[float] = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class GraphJob(SQLModel, table=True):
    id: str = Field(primary_key=True, max_length=36)
    status: JobStatus = Field(default=JobStatus.PENDING, max_length=20)

    #  Mathematical bounding parameters sent by user
    center_x: float
    center_y: float
    zoom: float
    max_iterations: int = Field(default=100)

    #  Storage for the generated mathematical graph plot image
    generated_graph: Optional[bytes] = Field(default=None, max_length=4_294_967_295) # LongBlob
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )


""" Input requests """
class FractalRequest(BaseModel):
    cx: float = PyField(default=DEFAULT_FRACTAL_CX, description="Real component center point on the complex numerical plane")
    cy: float = PyField(default=DEFAULT_FRACTAL_CY, description="Imaginary component center point on the complex plane")
    zoom: float = PyField(default=DEFAULT_FRACTAL_ZOOM, description="Magnification factor boundary scale")
    iterations: int = PyField(default=DEFAULT_FRACTAL_ITERATIONS, description="The loop exit cap limit for the escape velocity algorithm")
