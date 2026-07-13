"""
config.py

Central configuration for the GitHub Incident AI Platform.

Loads all environment variables from the .env file and
makes them available throughout the application.
"""

import os
from pathlib import Path
from dotenv import load_dotenv


# ----------------------------------------------------
# Project Root
# ----------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent


# ----------------------------------------------------
# Load Environment Variables
# ----------------------------------------------------

load_dotenv(BASE_DIR / ".env")


class Settings:
    """
    Application configuration.
    """

    # --------------------------------------------
    # Application
    # --------------------------------------------

    APP_NAME = "GitHub Incident AI Platform"

    VERSION = "1.0.0"

    DEBUG = True

    # --------------------------------------------
    # GitHub
    # --------------------------------------------

    GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")

    REPOSITORY = os.getenv(
        "GITHUB_REPOSITORY",
        "ullas-dev/incident-ai-demo"
    )

    GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")

    # --------------------------------------------
    # OpenAI
    # --------------------------------------------

    OPENAI_API_KEY = os.getenv(
        "OPENAI_API_KEY",
        ""
    )

    OPENAI_MODEL = "gpt-4.1"

    # --------------------------------------------
    # Database
    # --------------------------------------------

    DATABASE_PATH = BASE_DIR / "data" / "incident.db"

    # --------------------------------------------
    # Dashboard
    # --------------------------------------------

    PAGE_TITLE = "GitHub Incident Dashboard"

    PAGE_ICON = "🚨"


settings = Settings()