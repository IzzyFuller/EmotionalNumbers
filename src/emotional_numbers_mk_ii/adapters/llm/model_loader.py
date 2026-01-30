"""MLX model loading - singleton pattern for expensive model load."""

from __future__ import annotations

import os

# Singleton model state
_model = None
_tokenizer = None


def get_model():
    """Singleton model loading - expensive, do once."""
    global _model, _tokenizer
    if _model is None:
        from mlx_lm import load

        model_name = os.environ.get(
            "EMOTIONAL_NUMBERS_MLX_MODEL",
            "mlx-community/SmolLM2-1.7B-Instruct",
        )
        _model, _tokenizer = load(model_name)
    return _model, _tokenizer


def reset_model():
    """Reset singleton for testing."""
    global _model, _tokenizer
    _model = None
    _tokenizer = None
