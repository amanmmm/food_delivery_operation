
from src.ai.providers import get_provider


def summarize_issue(evidence: dict) -> str:
    """One stable interface for generating an operational summary."""
    return get_provider().summarize(evidence)
