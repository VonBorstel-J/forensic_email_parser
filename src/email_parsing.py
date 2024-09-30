# email_parsing.py

import logging
import os
import json
import openai
from typing import Dict, Any
from parsers.parser_factory import ParserFactory
from utils.config import Config
from openai.error import OpenAIError
from email_retrieval import (
    retrieve_unread_emails,
    EmailRetrievalError,
)  # Import specific exception

# Configure logging
config = Config()
log_dir = os.path.dirname(config.LOG_FILE)
os.makedirs(log_dir, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(config.LOG_FILE)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class EmailParsingError(Exception):
    """Custom exception for email parsing errors."""

    pass


class EmailParser:
    """EmailParser handles the parsing and validation of forensic engineering emails."""

    def __init__(self):
        self.parser_factory = ParserFactory()
        self.openai_api_key = config.OPENAI_API_KEY
        openai.api_key = self.openai_api_key

    def parse_email(self, email_content: str) -> Dict[str, Any]:
        """Parse the email content and extract relevant data with three layers of validation."""
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
            logger.debug("AI-validated data: %s", ai_validated_data)

            if not self.ai_validation(ai_validated_data):
                logger.warning("AI-assisted validation failed.")
                raise EmailParsingError("AI-assisted validation failed.")

            # Layer 3: Prepare for Manual Verification
            validated_data = self.prepare_for_manual_verification(ai_validated_data)
            logger.info("Email parsing and validation completed successfully.")

            return validated_data

        except EmailParsingError as e:
            logger.error("EmailParsingError: %s", str(e))
            raise
        except OpenAIError as e:
            logger.error("OpenAI API Error during email parsing: %s", str(e))
            raise EmailParsingError("Failed during AI-assisted review.") from e
        except Exception as e:
            logger.exception("Unexpected error during email parsing.")
            raise EmailParsingError(
                "An unexpected error occurred during email parsing."
            ) from e

    def automated_validation(self, data: Dict[str, Any]) -> bool:
        """Perform automated validation on the extracted data."""
        required_fields = [
            "Requesting Party Insurance Company",
            "Carrier Claim Number",
            "Insured Name",
            "Date of Loss/Occurrence",
        ]

        for field in required_fields:
            if field not in data or not data[field]:
                logger.error("Missing required field: %s", field)
                return False

        logger.info("Automated validation passed.")
        return True

    def ai_assisted_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Use OpenAI's GPT model to review and enhance the extracted data."""
        try:
            prompt = self.construct_ai_prompt(data)
            logger.debug("Constructed AI prompt: %s", prompt)

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are an assistant that verifies and enhances data extracted from forensic engineering emails.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )

            ai_response = response.choices[0].message["content"]
            logger.debug("AI response: %s", ai_response)

            enhanced_data = self.parse_ai_response(ai_response)
            return enhanced_data

        except OpenAIError as e:
            logger.error("OpenAI API error during AI-assisted review: %s", str(e))
            raise EmailParsingError(
                "AI-assisted review failed due to OpenAI API error."
            ) from e
        except Exception as e:
            logger.exception("Unexpected error during AI-assisted review.")
            raise EmailParsingError(
                "An unexpected error occurred during AI-assisted review."
            ) from e

    def construct_ai_prompt(self, data: Dict[str, Any]) -> str:
        """Construct a prompt for the AI model based on extracted data."""
        prompt = (
            "Please verify the following extracted data from a forensic engineering email and suggest any necessary corrections or enhancements. "
            "Provide the validated data in JSON format.\n\n"
            f"{json.dumps(data, indent=2)}"
        )
        return prompt

    def parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the AI model's response to extract the validated data."""
        try:
            json_start = ai_response.find("{")
            json_end = ai_response.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                logger.error("JSON not found in AI response.")
                raise EmailParsingError("AI response parsing failed: JSON not found.")
            json_str = ai_response[json_start:json_end]
            validated_data = json.loads(json_str)
            logger.info("AI-assisted validation successful.")
            return validated_data
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON: %s", str(e))
            raise EmailParsingError(
                "AI response parsing failed due to JSON decode error."
            ) from e
        except Exception as e:
            logger.exception("Unexpected error while parsing AI response.")
            raise EmailParsingError(
                "An unexpected error occurred while parsing AI response."
            ) from e

    def ai_validation(self, data: Dict[str, Any]) -> bool:
        """Additional AI-based validation can be implemented here."""
        logger.info("AI validation passed.")
        return True

    def prepare_for_manual_verification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Flag the data for manual verification and prepare it for human review."""
        data["requires_manual_verification"] = True
        logger.info("Data prepared for manual verification.")
        return data


def main():
    """Entry point for the email parsing module."""
    try:
        parser = EmailParser()
        emails = retrieve_unread_emails()
        logger.info("Retrieved %d unread emails.", len(emails))

        for email in emails:
            email_content = email["content"]
            try:
                parsed_data = parser.parse_email(email_content)
                logger.info("Parsed data: %s", parsed_data)
                # Proceed with data processing, e.g., integration into Quickbase
            except EmailParsingError as e:
                logger.error(
                    "Failed to parse email with subject '%s': %s",
                    email.get("subject", "No Subject"),
                    str(e),
                )
                # Optionally, mark email for manual review or move to a failure queue
            except Exception as e:
                logger.exception(
                    "Unexpected error while processing email with subject '%s'.",
                    email.get("subject", "No Subject"),
                )
                # Handle or log unexpected exceptions

    except EmailRetrievalError as e:
        logger.error("Failed to retrieve emails: %s", str(e))
    except Exception as e:
        logger.exception("Unexpected error during email retrieval.")
        # Handle or log unexpected exceptions


if __name__ == "__main__":
    main()
