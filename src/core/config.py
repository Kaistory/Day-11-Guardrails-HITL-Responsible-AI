"""
Lab 11 — Configuration & API Key Setup
"""
import os


# OpenAI model used across the lab.
#   OPENAI_MODEL  — plain name for the OpenAI SDK (attacks.py, NeMo config)
#   LITELLM_MODEL — same model prefixed for ADK's LiteLlm wrapper
OPENAI_MODEL = "gpt-4o-mini"
LITELLM_MODEL = f"openai/{OPENAI_MODEL}"


def setup_api_key():
    """Load OpenAI API key from environment or prompt."""
    if "OPENAI_API_KEY" not in os.environ:
        os.environ["OPENAI_API_KEY"] = input("Enter OpenAI API Key: ")
    print("API key loaded.")


# Allowed banking topics (used by topic_filter)
ALLOWED_TOPICS = [
    "banking", "account", "transaction", "transfer",
    "loan", "interest", "savings", "credit",
    "deposit", "withdrawal", "balance", "payment",
    "tai khoan", "giao dich", "tiet kiem", "lai suat",
    "chuyen tien", "the tin dung", "so du", "vay",
    "ngan hang", "atm",
]

# Blocked topics (immediate reject)
BLOCKED_TOPICS = [
    "hack", "exploit", "weapon", "drug", "illegal",
    "violence", "gambling", "bomb", "kill", "steal",
]
