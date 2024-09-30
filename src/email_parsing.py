# email_parsing.py

"""
Email Parsing Module

This module is responsible for parsing and validating the content of retrieved emails.
It employs both rule-based parsing and AI-assisted validation using OpenAI's GPT-4 model
to ensure the extracted data meets specific criteria.
"""

import logging
import os
import json
from pathlib import Path
from typing import Dict, Any

import openai
from openai import OpenAIError

from parsers.parser_factory import ParserFactory
from utils.config import Config

# Import the email retrieval module
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
        """
        Initializes the EmailParser with necessary dependencies.

        :param parser_factory: An instance of ParserFactory.
        :param config: An instance of Config for configuration settings.
        """
        self.parser_factory = parser_factory or ParserFactory()
        self.config = config or Config()
        self.openai_api_key = self.config.OPENAI_API_KEY
        openai.api_key = self.openai_api_key

    def parse_email(self, email_content: str) -> Dict[str, Any]:
        """
        Parses the email content and extracts relevant data with validation.

        :param email_content: The content of the email to parse.
        :return: Validated and possibly enriched data extracted from the email.
        :raises EmailParsingError: If parsing or validation fails.
        """
        try:
            logger.info("Starting email parsing process.")

            # Layer 1: Automated Validation using Rule-Based Parser
            parser = self.parser_factory.get_parser(email_content)
            logger.info("Selected parser: %s", parser.__class__.__name__)
            extracted_data = parser.parse(email_content)
            logger.debug("Extracted data from parser: %s", extracted_data)

            if not self.automated_validation(extracted_data):
                logger.warning("Automated validation failed.")
                raise EmailParsingError("Automated validation failed.")

            # Layer 2: AI-Assisted Review using LLM
            ai_validated_data = self.ai_assisted_review(extracted_data)

            logger.info("Email parsing and validation successful.")
            return ai_validated_data
        except (EmailParsingError, OpenAIError, EmailRetrievalError) as e:
            logger.error("Error in email parsing: %s", str(e))
            raise EmailParsingError(f"Error in email parsing: {str(e)}") from e

    def automated_validation(self, extracted_data: Dict[str, Any]) -> bool:
        """
        Performs basic validation on the extracted data.

        :param extracted_data: The data extracted from the email.
        :return: True if validation passes, False otherwise.
        """
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
        """
        Performs AI-assisted validation using OpenAI's GPT model.

        :param extracted_data: The data extracted from the email.
        :return: Validated and possibly enriched data.
        :raises EmailParsingError: If AI-assisted validation fails.
        """
        try:
            prompt = self.construct_prompt(extracted_data)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant specialized in validating extracted data from emails.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )  # pylint: disable=no-member
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
        """
        Constructs a detailed prompt for LLM validation.

        :param extracted_data: The data extracted from the email.
        :return: The constructed prompt string.
        """
        prompt = (
            "You are an assistant specialized in validating extracted data from emails. "
            "Please review the following fields for accuracy, completeness, and consistency. "
            "If any discrepancies are found, highlight them and suggest corrections. "
            "Provide the validated data in well-formatted JSON.\n\n"
        )
        for key, value in extracted_data.items():
            prompt += f"{key}: {value}\n"
        return prompt


def process_emails():
    """
    Retrieves unread emails, parses and validates them, and marks them as read upon successful processing.
    """
    try:
        # Retrieve unread emails
        unread_emails = retrieve_unread_emails(max_results=100)
        logger.info("Number of unread emails retrieved: %d", len(unread_emails))

        if not unread_emails:
            logger.info("No unread emails to process.")
            return

        # Initialize the parser
        parser = EmailParser()

        for email in unread_emails:
            email_id = email.get("id")
            try:
                # Extract email content (assuming 'snippet' contains the necessary info)
                email_content = email.get("snippet", "")
                parsed_data = parser.parse_email(email_content)
                logger.info("Parsed data for email ID %s: %s", email_id, parsed_data)

                # Further processing can be done here (e.g., storing data in a database)

                # Mark the email as read after successful processing
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
                # Optionally, implement retry logic or flag the email for manual review

    except EmailRetrievalError as e:
        logger.error("Failed to process emails: %s", e)
    except Exception as e:
        logger.error("An unexpected error occurred: %s", e)


if __name__ == "__main__":
    process_emails()
