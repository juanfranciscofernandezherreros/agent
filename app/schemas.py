from pydantic import BaseModel, Field, HttpUrl
from typing import Any

class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    git_url: str = Field(min_length=8, max_length=500)

class EquivalenceRequest(BaseModel):
    original_url: HttpUrl
    reconstructed_url: HttpUrl
    cases: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    timeout_seconds: float = Field(default=10, ge=1, le=60)
