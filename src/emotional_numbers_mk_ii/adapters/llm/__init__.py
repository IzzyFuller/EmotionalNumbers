"""LLM adapters using MLX."""

from emotional_numbers_mk_ii.adapters.llm.model_loader import get_model, reset_model
from emotional_numbers_mk_ii.adapters.llm.questions_adapter import (
    LLMQuestionsAdapter,
    QuestionParseError,
)
from emotional_numbers_mk_ii.adapters.llm.rules_adapter import (
    LLMRulesAdapter,
    RuleValidationError,
)

# Backward compatibility aliases
MLXQuestionGenerator = LLMQuestionsAdapter
MLXRuleGenerator = LLMRulesAdapter
_reset_model = reset_model

__all__ = [
    "LLMQuestionsAdapter",
    "LLMRulesAdapter",
    "QuestionParseError",
    "RuleValidationError",
    "get_model",
    "reset_model",
    # Backward compatibility
    "MLXQuestionGenerator",
    "MLXRuleGenerator",
    "_reset_model",
]
