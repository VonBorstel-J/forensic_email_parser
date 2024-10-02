# src/utils/config.py

import os
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()


class Config:
    # Gmail API Credentials
    CREDENTIALS_PATH = os.getenv("CREDENTIALS_PATH")
    TOKEN_PATH = os.getenv("TOKEN_PATH")

    # Logging
    LOG_FILE = os.getenv("LOG_FILE", "logs/email_retrieval.log")

    # Quickbase API
    QUICKBASE_API_URL = os.getenv(
        "QUICKBASE_API_URL"
    )  # e.g., "https://api.quickbase.com/v1/records"
    QUICKBASE_USER_TOKEN = os.getenv("QUICKBASE_USER_TOKEN")
    QUICKBASE_REALM_HOSTNAME = os.getenv(
        "QUICKBASE_REALM_HOSTNAME"
    )  # e.g., "yourrealm.quickbase.com"
    QUICKBASE_TABLE_ID = os.getenv("QUICKBASE_TABLE_ID")  # e.g., "bq9f8asdf"

    # Flask Configuration
    FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY")

    # OpenAI API
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

    # Local LLM Configuration
    USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "False").lower() in ("true", "1", "t")
    LOCAL_LLM_API_ENDPOINT = os.getenv(
        "LOCAL_LLM_API_ENDPOINT"
    )  # e.g., "http://localhost:8000/v1/chat/completions"

    # JWT Configuration
    JWT_SECRET_KEY = os.getenv(
        "JWT_SECRET_KEY", "default_secret_key"
    )  # Replace default in production
    JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES = int(
        os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )


# Setup logging configuration
logging.basicConfig(
    filename=Config.LOG_FILE,
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# Example logging usage
if __name__ == "__main__":
    logger = logging.getLogger("ConfigTest")
    logger.info("Configuration loaded successfully.")
