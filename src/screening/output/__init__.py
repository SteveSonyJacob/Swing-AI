"""Output and pipeline dispatchers for Agent 1."""

from src.screening.output.formatter import (
    format_screening_output,
    format_screening_error,
    print_screening_summary_table
)
from src.screening.output.pipeline import pipe_to_agents

__all__ = [
    "format_screening_output",
    "format_screening_error",
    "print_screening_summary_table",
    "pipe_to_agents"
]
