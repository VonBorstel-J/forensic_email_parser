# src/email_parsing.py

import logging
from typing import List, Dict, Any

import openai

from parsers.parser_factory import ParserFactory
from utils.config import Config

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.FileHandler(Config.LOG_FILE)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)


class EmailParsingError(Exception):
    """Custom exception for email parsing errors."""
    pass


class EmailParser:
    def __init__(self):
        self.parser_factory = ParserFactory()
        self.openai_api_key = Config.OPENAI_API_KEY
        openai.api_key = self.openai_api_key

    def parse_email(self, email_content: str) -> Dict[str, Any]:
        """
        Parse the email content and extract relevant data with three layers of validation.

        :param email_content: The raw content of the email.
        :return: A dictionary containing the extracted and validated data.
        """
        try:
            logger.info("Starting email parsing process.")

            # Layer 1: Automated Validation using Rule-Based Parser
            parser = self.parser_factory.get_parser(email_content)
            logger.info(f"Selected parser: {parser.__class__.__name__}")
            extracted_data = parser.parse(email_content)
            logger.debug(f"Extracted data from parser: {extracted_data}")

            if not self.automated_validation(extracted_data):
                logger.warning("Automated validation failed.")
                raise EmailParsingError("Automated validation failed.")

            # Layer 2: AI-Assisted Review using LLM
            ai_validated_data = self.ai_assisted_review(extracted_data)
            logger.debug(f"AI-validated data: {ai_validated_data}")

            if not self.ai_validation(ai_validated_data):
                logger.warning("AI-assisted validation failed.")
                raise EmailParsingError("AI-assisted validation failed.")

            # Layer 3: Prepare for Manual Verification
            validated_data = self.prepare_for_manual_verification(ai_validated_data)
            logger.info("Email parsing and validation completed successfully.")

            return validated_data

        except Exception as e:
            logger.error(f"Error during email parsing: {str(e)}")
            raise

    def automated_validation(self, data: Dict[str, Any]) -> bool:
        """
        Perform automated validation on the extracted data.

        :param data: Extracted data dictionary.
        :return: Boolean indicating if validation passed.
        """
        # Example validation rules
        required_fields = [
            "Requesting Party Insurance Company",
            "Claim Number",
            "Insured Information",
            "Assignment Information",
            "Date of Loss"
        ]

        for field in required_fields:
            if field not in data or not data[field]:
                logger.error(f"Missing required field: {field}")
                return False

        logger.info("Automated validation passed.")
        return True

    def ai_assisted_review(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use OpenAI's GPT model to review and enhance the extracted data.

        :param data: Extracted data dictionary.
        :return: Enhanced data dictionary.
        """
        try:
            prompt = self.construct_ai_prompt(data)
            logger.debug(f"Constructed AI prompt: {prompt}")

            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an assistant that verifies and enhances data extracted from forensic engineering emails."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )

            ai_response = response.choices[0].message['content']
            logger.debug(f"AI response: {ai_response}")

            # Assuming AI returns a JSON-formatted string
            enhanced_data = self.parse_ai_response(ai_response)
            return enhanced_data

        except Exception as e:
            logger.error(f"AI-assisted review failed: {str(e)}")
            raise EmailParsingError("AI-assisted review failed.") from e

    def construct_ai_prompt(self, data: Dict[str, Any]) -> str:
        """
        Construct a prompt for the AI model based on extracted data.

        :param data: Extracted data dictionary.
        :return: AI prompt string.
        """
        prompt = (
            "Please verify the following extracted data from a forensic engineering email and suggest any necessary corrections or enhancements. "
            "Provide the validated data in JSON format.\n\n"
            f"{data}"
        )
        return prompt

    def parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse the AI model's response to extract the validated data.

        :param ai_response: The raw response string from the AI model.
        :return: Validated data dictionary.
        """
        import json
        try:
            # Extract JSON part from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            json_str = ai_response[json_start:json_end]
            validated_data = json.loads(json_str)
            logger.info("AI-assisted validation successful.")
            return validated_data
        except json.JSONDecodeError as e:
            logger.error("Failed to parse AI response as JSON.")
            raise EmailParsingError("AI response parsing failed.") from e

    def ai_validation(self, data: Dict[str, Any]) -> bool:
        """
        Additional AI-based validation can be implemented here.

        :param data: Data to validate.
        :return: Boolean indicating if AI validation passed.
        """
        # Placeholder for any additional AI-based validations
        logger.info("AI validation passed.")
        return True

    def prepare_for_manual_verification(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Flag the data for manual verification and prepare it for human review.

        :param data: Validated data dictionary.
        :return: Data dictionary with a flag for manual verification.
        """
        data['requires_manual_verification'] = True
        logger.info("Data prepared for manual verification.")
        return data


def main():
    """
    Entry point for the email parsing module.
    This can be invoked by other modules or scheduled tasks.
    """
    from email_retrieval import retrieve_unread_emails

    parser = EmailParser()
    try:
        emails = retrieve_unread_emails()
        logger.info(f"Retrieved {len(emails)} unread emails.")

        for email in emails:
            email_content = email['content']  # Assuming email dict has 'content'
            parsed_data = parser.parse_email(email_content)
            # Here, you would typically pass parsed_data to the next module
            logger.info(f"Parsed data: {parsed_data}")
            # Example: Save to database or queue for manual verification

    except Exception as e:
        logger.error(f"Failed to parse emails: {str(e)}")


if __name__ == "__main__":
    main()
