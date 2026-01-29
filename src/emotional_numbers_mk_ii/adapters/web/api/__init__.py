"""API module - routes and models for the game API."""

from emotional_numbers_mk_ii.adapters.web.api.models import (
    AnswersRequest,
    AnswersResponse,
    CellModel,
    ClassifyRequest,
    ClassifyResponse,
    ClearResponse,
    HintResponse,
    QuestionModel,
    RegionHint,
    SelectRequest,
    SelectResponse,
    StartResponse,
    StateResponse,
)
from emotional_numbers_mk_ii.adapters.web.api.routes import (
    GameSession,
    get_session,
    router,
    set_session,
)

__all__ = [
    # Models
    "AnswersRequest",
    "AnswersResponse",
    "CellModel",
    "ClassifyRequest",
    "ClassifyResponse",
    "ClearResponse",
    "HintResponse",
    "QuestionModel",
    "RegionHint",
    "SelectRequest",
    "SelectResponse",
    "StartResponse",
    "StateResponse",
    # Routes
    "GameSession",
    "get_session",
    "router",
    "set_session",
]
