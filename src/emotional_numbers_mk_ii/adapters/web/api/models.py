"""Pydantic request/response models for the game API."""

from pydantic import BaseModel, ConfigDict


# ============================================================================
# Request Models
# ============================================================================


class AnswersRequest(BaseModel):
    answers: list[dict]


class SelectRequest(BaseModel):
    x: int
    y: int


class ClassifyRequest(BaseModel):
    bucket: str


# ============================================================================
# Response Models
# ============================================================================


class QuestionModel(BaseModel):
    id: str
    text: str


class StartResponse(BaseModel):
    phase: str
    questions: list[QuestionModel]


class CellModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    x: int
    y: int
    value: int
    selected: bool
    classified: bool


class AnswersResponse(BaseModel):
    phase: str
    grid: list[list[CellModel]]


class StateResponse(BaseModel):
    grid: list[list[CellModel]]
    bins: dict[str, int]
    progress: int


class SelectResponse(BaseModel):
    selected: list[list[int]]


class ClearResponse(BaseModel):
    selected: list[list[int]]


class ClassifyResponse(BaseModel):
    success: bool
    classified_count: int
    progress: int
    bins: dict[str, int]


class RegionHint(BaseModel):
    bucket: str
    positions: list[list[int]]


class HintResponse(BaseModel):
    region: RegionHint | None = None
    message: str | None = None
