#src\email_parsing.py

"""
This module handles the parsing and validation of forensic engineering emails.
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any

import openai  # noqa: E1101 - Ignore Pylint no-member error for now
from openai import OpenAIError

from parsers.parser_factory import ParserFactory
from utils.config import Config
from email_retrieval import (
    retrieve_unread_emails,
    EmailRetrievalError,
    EmailRetrievalModule,
)

# Configure logging
config = Config()
log_dir = Path(config.LOG_FILE).parent
log_dir.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(config.LOG_FILE)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
if not logger.handlers:
    logger.addHandler(handler)


class EmailParsingError(Exception):
    """Custom exception for email parsing errors."""

    pass


class EmailParser:
    """Handles the parsing and validation of forensic engineering emails."""

    def __init__(self, parser_factory: ParserFactory = None, config: Config = None):
        self.parser_factory = parser_factory or ParserFactory()
        self.config = config or Config()
        self.openai_api_key = self.config.OPENAI_API_KEY
        openai.api_key = self.openai_api_key

    def parse_email(
        self, email_id: str, email_content: str, user_preferences: dict = None
    ) -> Dict[str, Any]:
        """
        Parses the email content and extracts relevant data with validation.
        """
        try:
            logger.info("Starting parsing for email ID %s.", email_id)

            parser = self.parser_factory.get_parser(
                email_content, email_id, user_preferences
            )
            logger.info(
                "Email ID %s: Selected parser %s", email_id, parser.__class__.__name__
            )
            extracted_data = parser.parse(email_content)
            logger.debug("Email ID %s: Extracted data: %s", email_id, extracted_data)

            if not self.automated_validation(extracted_data):
                logger.warning("Automated validation failed for email ID %s.", email_id)
                raise EmailParsingError("Automated validation failed.")

            ai_validated_data = self.ai_assisted_review(extracted_data)

            logger.info(
                "Email parsing and validation successful for email ID %s.", email_id
            )
            return ai_validated_data
        except (EmailParsingError, OpenAIError, EmailRetrievalError) as e:
            logger.error("Error parsing email ID %s: %s", email_id, str(e))
            raise EmailParsingError(
                f"Error parsing email ID {email_id}: {str(e)}"
            ) from e

    def automated_validation(self, extracted_data: Dict[str, Any]) -> bool:
        required_fields = [
            "Carrier Claim Number",
            "Insured Information",
            "Adjuster Information",
        ]
        for field in required_fields:
            if not extracted_data.get(field):
                logger.error("Missing required field: %s", field)
                return False
        logger.info("Automated validation passed.")
        return True

    def ai_assisted_review(self, extracted_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            prompt = self.construct_prompt(extracted_data)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant specialized in validating extracted data.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            validated_data = json.loads(response.choices[0].message["content"])
            logger.debug("AI-assisted validated data: %s", validated_data)
            return validated_data
        except OpenAIError as e:
            logger.error("OpenAI error: %s", str(e))
            raise EmailParsingError(f"OpenAI error: {str(e)}") from e
        except json.JSONDecodeError as e:
            logger.error("Failed to decode OpenAI response: %s", str(e))
            raise EmailParsingError(
                f"Failed to decode OpenAI response: {str(e)}"
            ) from e

    def construct_prompt(self, extracted_data: Dict[str, Any]) -> str:
        prompt = "Please validate the following extracted data for accuracy and consistency:\n\n"
        for key, value in extracted_data.items():
            prompt += f"{key}: {value}\n"
        return prompt


def process_emails():
    """
    Retrieves unread emails, parses and validates them, and marks them as read upon successful processing.
    """
    try:
        unread_emails = retrieve_unread_emails(max_results=100)
        logger.info("Number of unread emails retrieved: %d", len(unread_emails))

        if not unread_emails:
            logger.info("No unread emails to process.")
            return

        parser = EmailParser()

        for email in unread_emails:
            email_id = email.get("id")
            try:
                email_content = email.get("snippet", "")
                user_preferences = {}

                parsed_data = parser.parse_email(
                    email_id, email_content, user_preferences
                )
                logger.info("Parsed data for email ID %s: %s", email_id, parsed_data)

                email_module = EmailRetrievalModule(
                    credentials_path=Path(
                        os.getenv("CREDENTIALS_PATH", "credentials/credentials.json")
                    ),
                    token_path=Path(os.getenv("TOKEN_PATH", "token.pickle")),
                )
                email_module.mark_as_read(email_id)
                logger.info("Email ID %s marked as read.", email_id)

            except EmailParsingError as e:
                logger.error("Parsing failed for email ID %s: %s", email_id, e)
            except Exception as e:
                logger.exception(
                    "Unexpected error processing email ID %s: %s", email_id, e
                )

    except EmailRetrievalError as e:
        logger.error("Failed to retrieve emails: %s", e)
    except Exception as e:
        logger.exception("An unexpected error occurred while processing emails.")
