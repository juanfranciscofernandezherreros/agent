from pydantic import BaseModel, Field, HttpUrl
from typing import Any

class ProjectCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    git_url: str = Field(min_length=8, max_length=500)

class RepositoryInput(BaseModel):
    name: str = Field(min_length=2, max_length=200)
    git_url: str = Field(min_length=8, max_length=1000)

class AnalysisGroupCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    repositories: list[RepositoryInput] = Field(min_length=1, max_length=100)

class GitLabGroupAnalysisCreate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    # None means all projects; an explicit list limits the run to selected GitLab project IDs.
    project_ids: list[int] | None = Field(default=None, min_length=1, max_length=100)

class EquivalenceRequest(BaseModel):
    original_url: HttpUrl
    reconstructed_url: HttpUrl
    cases: list[dict[str, Any]] = Field(min_length=1, max_length=100)
    timeout_seconds: float = Field(default=10, ge=1, le=60)

class CodeGenerationRequest(BaseModel):
    brief: str = Field(min_length=20, max_length=12000)
    max_files: int = Field(default=12, ge=1, le=20)

class StateSnapshotComparisonRequest(BaseModel):
    original: dict[str, Any]
    reconstructed: dict[str, Any]

class RepairRequest(BaseModel):
    equivalence_run_id: str = Field(min_length=1, max_length=80)
    max_files: int = Field(default=5, ge=1, le=10)
