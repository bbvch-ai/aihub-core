"""
Shared LLM utilities for whitepaper generation scripts.

Provides:
- CLI colors for terminal output
- LLM invocation via the `llm` CLI tool
- Cost tracking based on Gemini API pricing
"""

import json
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""

    _RED = "\033[0;31m"
    _GREEN = "\033[0;32m"
    _YELLOW = "\033[1;33m"
    _BLUE = "\033[0;34m"
    _NC = "\033[0m"

    @classmethod
    def red(cls, text: str) -> str:
        """Wrap text in red."""
        return f"{cls._RED}{text}{cls._NC}"

    @classmethod
    def green(cls, text: str) -> str:
        """Wrap text in green."""
        return f"{cls._GREEN}{text}{cls._NC}"

    @classmethod
    def yellow(cls, text: str) -> str:
        """Wrap text in yellow."""
        return f"{cls._YELLOW}{text}{cls._NC}"

    @classmethod
    def blue(cls, text: str) -> str:
        """Wrap text in blue."""
        return f"{cls._BLUE}{text}{cls._NC}"


def call_llm(prompt: str, model: str) -> tuple[bool, str]:
    """
    Call LLM with the given prompt using the `llm` CLI tool.

    Args:
        prompt: The prompt text to send
        model: The model identifier (e.g., "gemini-3-flash-preview")

    Returns:
        Tuple of (success: bool, output: str)
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as tmp:
        tmp.write(prompt)
        tmp_path = tmp.name

    try:
        with open(tmp_path, "r") as f:
            result = subprocess.run(
                ["llm", "--no-stream", "-m", model],
                stdin=f,
                capture_output=True,
                text=True,
                timeout=300,
            )
        return (result.returncode == 0, result.stdout if result.returncode == 0 else result.stderr)
    finally:
        Path(tmp_path).unlink(missing_ok=True)


# Gemini pricing per million tokens (USD)
# Source: https://ai.google.dev/gemini-api/docs/pricing
GEMINI_PRICING: dict[str, tuple[float, float]] = {
    # (input_price, output_price) per million tokens
    "gemini-3-pro-preview": (2.00, 12.00),
    "gemini-3-flash-preview": (0.50, 3.00),
    "gemini-2.5-pro": (1.25, 10.00),
    "gemini-2.5-flash": (0.30, 2.50),
    "gemini-2.5-flash-lite": (0.10, 0.40),
    "gemini-2.0-flash": (0.10, 0.40),
    "gemini-2.0-flash-lite": (0.075, 0.30),
}


def get_last_llm_usage() -> tuple[int, int]:
    """Get token usage from the last LLM call via llm logs."""
    try:
        result = subprocess.run(
            ["llm", "logs", "-n", "1", "--json"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0:
            logs = json.loads(result.stdout)
            if logs:
                entry = logs[0]
                return (
                    entry.get("input_tokens", 0) or 0,
                    entry.get("output_tokens", 0) or 0,
                )
    except Exception:
        pass  # Best effort - return zeros if llm CLI unavailable or output unparseable
    return (0, 0)


@dataclass
class UsageTracker:
    """Tracks token usage and costs across LLM calls."""

    total_input_tokens: int = 0
    total_output_tokens: int = 0
    call_count: int = 0
    model: str = ""

    def add_usage(self, input_tokens: int, output_tokens: int) -> None:
        """Add usage from an LLM call."""
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens
        self.call_count += 1

    def track_last_call(self) -> None:
        """Track usage from the most recent LLM call."""
        input_tokens, output_tokens = get_last_llm_usage()
        self.add_usage(input_tokens, output_tokens)

    def get_cost_estimate(self) -> float:
        """Calculate estimated cost in USD based on Gemini pricing."""
        input_price, output_price = 1.0, 5.0  # Default fallback

        for model_key, prices in GEMINI_PRICING.items():
            if model_key in self.model or self.model in model_key:
                input_price, output_price = prices
                break

        input_cost = (self.total_input_tokens / 1_000_000) * input_price
        output_cost = (self.total_output_tokens / 1_000_000) * output_price
        return input_cost + output_cost

    def format_summary(self) -> str:
        """Return formatted usage summary string."""
        if self.call_count == 0:
            return ""

        cost = self.get_cost_estimate()
        return (
            f"\n💰 Usage Summary\n"
            f"{'─' * 40}\n"
            f"  LLM Calls:      {self.call_count}\n"
            f"  Input tokens:   {self.total_input_tokens:,}\n"
            f"  Output tokens:  {self.total_output_tokens:,}\n"
            f"  Total tokens:   {self.total_input_tokens + self.total_output_tokens:,}\n"
            f"  Est. cost:      ${cost:.4f} USD"
        )
