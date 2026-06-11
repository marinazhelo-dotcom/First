from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum
from datetime import datetime, UTC, timezone


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


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
    generated_graph: Optional[bytes] = Field(default=None, max_length=16_777_215) # Medium/LongBlob
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
