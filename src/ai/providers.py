
import os
import requests


class LocalRuleProvider:
    """Works offline and uses only supplied operational evidence."""

    def summarize(self, evidence: dict) -> str:
        issue = evidence.get(
            "top_issue", "No dominant issue"
        )

        detail = evidence.get(
            "detail",
            "There is not enough evidence to isolate a bottleneck."
        )

        action = evidence.get(
            "recommended_action",
            "Continue monitoring daily performance."
        )

        return (
            f"**Main finding:** {issue}. {detail}\n\n"
            f"**Suggested action:** {action}"
        )


class OllamaProvider:
    """Optional locally hosted language model."""

    def summarize(self, evidence: dict) -> str:
        model = os.getenv("OLLAMA_MODEL", "llama3.2")

        url = os.getenv(
            "OLLAMA_URL",
            "http://localhost:11434/api/generate"
        )

        prompt = (
            "You are a food delivery operations analyst. "
            "Use only the supplied aggregate evidence. "
            "Do not invent numbers. Explain the main issue "
            "and suggest one practical action in 2-3 sentences.\n"
            f"Evidence: {evidence}"
        )

        response = requests.post(
            url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=25
        )

        response.raise_for_status()

        result = response.json().get("response", "").strip()

        return result or LocalRuleProvider().summarize(evidence)


def get_provider():
    provider_name = os.getenv("AI_PROVIDER", "local").lower()

    if provider_name == "ollama":
        return OllamaProvider()

    return LocalRuleProvider()
