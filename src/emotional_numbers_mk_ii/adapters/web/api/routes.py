"""API routes for the game."""

from fastapi import APIRouter, Depends

from emotional_numbers_mk_ii.adapters.web.api.models import (
    AnswersRequest,
    AnswersResponse,
    BehaviorModel,
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
from emotional_numbers_mk_ii.adapters.llm.mlx_adapter import (
    MLXQuestionGenerator,
    MLXRuleGenerator,
)
from emotional_numbers_mk_ii.domain.game import Game, answers_to_seed

router = APIRouter(prefix="/api")


# ============================================================================
# Session State Protocol
# ============================================================================


class GameSession:
    """Manages game session state."""

    def __init__(
        self,
        question_generator: MLXQuestionGenerator | None = None,
        rule_generator: MLXRuleGenerator | None = None,
    ):
        self.phase = "welcome"
        self.questions: list[dict] = []
        self.game: Game | None = None
        self._question_generator = question_generator or MLXQuestionGenerator()
        self._rule_generator = rule_generator or MLXRuleGenerator()

    def start(self) -> list[dict]:
        """Start a new session, generate questions via LLM."""
        self.phase = "onboarding"
        self.questions = self._question_generator.generate_questions()
        self.game = None
        return self.questions

    def submit_answers(self, answers: list[dict]) -> Game:
        """Submit answers, create game."""
        seed = answers_to_seed(answers)
        rule_set = self._rule_generator.generate_rules(answers, rows=25, cols=40)
        self.game = Game(rows=25, cols=40, rule_set=rule_set, seed=seed)
        self.phase = "playing"
        return self.game


# Module-level session (set by app.py)
_session: GameSession | None = None


def get_session() -> GameSession:
    """Dependency to get session."""
    return _session  # type: ignore[return-value]


def set_session(session: GameSession) -> None:
    """Set the module session (called by app.py)."""
    global _session
    _session = session


# ============================================================================
# Helpers
# ============================================================================


def _cell_to_model(cell, rule_set) -> CellModel:
    """Convert domain Cell to CellModel with behavior info."""
    behavior = rule_set.get_behavior_for_position(cell.x, cell.y)
    in_region = behavior is not None
    return CellModel(
        x=cell.x,
        y=cell.y,
        value=cell.value,
        selected=cell.selected,
        classified=cell.classified,
        in_region=in_region,
        jiggle_intensity=behavior.jiggle_intensity if in_region else 0.15,
        jiggle_frequency=behavior.jiggle_frequency if in_region else 0.8,
        sound_id=behavior.sound_id if in_region else "tone_00",
    )


# ============================================================================
# Routes
# ============================================================================


@router.post("/start", response_model=StartResponse)
async def start_game(session: GameSession = Depends(get_session)) -> StartResponse:
    """Start a new game session, return onboarding questions."""
    questions = session.start()
    return StartResponse(
        phase=session.phase,
        questions=[QuestionModel(**q) for q in questions],
    )


@router.post("/answers", response_model=AnswersResponse)
async def submit_answers(
    request: AnswersRequest,
    session: GameSession = Depends(get_session),
) -> AnswersResponse:
    """Submit onboarding answers, generate puzzle and start game."""
    game = session.submit_answers(request.answers)
    return AnswersResponse(
        phase=session.phase,
        grid=[
            [_cell_to_model(cell, game.rule_set) for cell in row]
            for row in game.grid
        ],
    )


@router.get("/state", response_model=StateResponse)
async def get_state(session: GameSession = Depends(get_session)) -> StateResponse:
    """Get current game state."""
    return StateResponse(
        grid=[
            [_cell_to_model(cell, session.game.rule_set) for cell in row]
            for row in session.game.grid
        ],
        bins=session.game.bins,
        progress=session.game.progress,
        behaviors=[
            BehaviorModel(
                bucket=b.bucket,
                jiggle_intensity=b.jiggle_intensity,
                jiggle_frequency=b.jiggle_frequency,
                sound_id=b.sound_id,
            )
            for b in session.game.rule_set.behaviors
        ],
    )


@router.post("/select", response_model=SelectResponse)
async def toggle_selection(
    request: SelectRequest,
    session: GameSession = Depends(get_session),
) -> SelectResponse:
    """Toggle selection of a cell."""
    session.game.toggle_selection(request.x, request.y)
    return SelectResponse(
        selected=[list(pos) for pos in session.game.selected_positions],
    )


@router.post("/clear", response_model=ClearResponse)
async def clear_selection(session: GameSession = Depends(get_session)) -> ClearResponse:
    """Clear all selections."""
    session.game.clear_selection()
    return ClearResponse(selected=[])


@router.post("/classify", response_model=ClassifyResponse)
async def classify_selection(
    request: ClassifyRequest,
    session: GameSession = Depends(get_session),
) -> ClassifyResponse:
    """Classify selected cells to a bucket."""
    success, count = session.game.classify(request.bucket.upper())
    return ClassifyResponse(
        success=success,
        classified_count=count,
        progress=session.game.progress,
        bins=session.game.bins,
    )


@router.get("/hint", response_model=HintResponse)
async def get_hint(session: GameSession = Depends(get_session)) -> HintResponse:
    """Get a hint about an unclassified region."""
    hint = session.game.get_hint()
    return HintResponse(
        region=RegionHint(
            bucket=hint["bucket"],
            positions=[list(pos) for pos in hint["positions"]],
        ) if hint else None,
    )
