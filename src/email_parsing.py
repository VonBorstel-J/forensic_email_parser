import os
import logging
import re
import json
from pathlib import Path
from typing import Dict, Any, List

import spacy
import openai
from email import policy
from email.parser import BytesParser

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve paths and API keys from environment variables
LOG_FILE = Path(os.getenv('LOG_FILE', '../logs/email_parsing.log'))
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# Set OpenAI API key
openai.api_key = OPENAI_API_KEY

class EmailParsingModule:
    def __init__(self, nlp_model: str = 'en_core_web_sm', llm_model: str = 'gpt-4'):
        """
        Initializes the Email Parsing Module with the specified spaCy model and LLM model.

        :param nlp_model: The spaCy language model to use.
        :param llm_model: The LLM model to use for parsing.
        """
        try:
            self.nlp = spacy.load(nlp_model)
            logging.info(f"Loaded spaCy model: {nlp_model}")
        except Exception as e:
            logging.error(f"Failed to load spaCy model '{nlp_model}': {e}")
            raise e

        self.llm_model = llm_model
        logging.info(f"Configured LLM model: {llm_model}")

    def extract_with_llm(self, email_body: str) -> Dict[str, Any]:
        """
        Uses LLM to extract relevant data fields from the email body.

        :param email_body: The plain text content of the email.
        :return: A dictionary containing extracted data fields.
        """
        prompt = self.construct_prompt(email_body)
        try:
            response = openai.ChatCompletion.create(
                model=self.llm_model,
                messages=[
                    {"role": "system", "content": "You are a data extraction assistant."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1500,
                n=1,
                stop=None,
            )
            extracted_data = json.loads(response.choices[0].message['content'].strip())
            logging.info("Successfully extracted data using LLM.")
            return extracted_data
        except Exception as e:
            logging.error(f"LLM extraction failed: {e}")
            return {}

    def construct_prompt(self, email_body: str) -> str:
        """
        Constructs the prompt to send to the LLM for data extraction.

        :param email_body: The plain text content of the email.
        :return: The formatted prompt string.
        """
        prompt = (
            "Extract the following fields from the email content below. "
            "Provide the output in JSON format with the exact field names as specified. "
            "If a field is not present, set its value to null.\n\n"
            "Email Content:\n"
            f"{email_body}\n\n"
            "Fields to Extract:\n"
            "- Requesting Party:\n"
            "  - Insurance Company\n"
            "  - Handler\n"
            "  - Carrier Claim Number\n"
            "- Insured Information:\n"
            "  - Name\n"
            "  - Contact #\n"
            "  - Loss Address\n"
            "  - Public Adjuster\n"
            "  - Is the insured an Owner or a Tenant of the loss location?\n"
            "- Adjuster Information:\n"
            "  - Adjuster Name\n"
            "  - Adjuster Phone Number\n"
            "  - Adjuster Email\n"
            "  - Job Title\n"
            "  - Address\n"
            "  - Policy #\n"
            "- Assignment Information:\n"
            "  - Date of Loss/Occurrence\n"
            "  - Cause of loss\n"
            "  - Facts of Loss\n"
            "  - Loss Description\n"
            "  - Residence Occupied During Loss\n"
            "  - Was Someone home at time of damage\n"
            "  - Repair or Mitigation Progress\n"
            "  - Type\n"
            "  - Inspection type\n"
            "  - Wind\n"
            "  - Structural\n"
            "  - Hail\n"
            "  - Foundation\n"
            "  - Other - provide details\n"
            "  - Additional details/Special Instructions\n"
            "  - Attachments\n"
            "\n"
            "Example Output:\n"
            "{\n"
            '  "Requesting Party": {\n'
            '    "Insurance Company": "ABC Insurance",\n'
            '    "Handler": "John Doe",\n'
            '    "Carrier Claim Number": "12345"\n'
            '  },\n'
            '  "Insured Information": {\n'
            '    "Name": "Jane Smith",\n'
            '    "Contact #": "555-1234",\n'
            '    "Loss Address": "123 Elm Street",\n'
            '    "Public Adjuster": "Yes",\n'
            '    "Is the insured an Owner or a Tenant of the loss location?": "Owner"\n'
            '  },\n'
            '  "Adjuster Information": {\n'
            '    "Adjuster Name": "Mike Johnson",\n'
            '    "Adjuster Phone Number": "555-5678",\n'
            '    "Adjuster Email": "mike.johnson@example.com",\n'
            '    "Job Title": "Senior Adjuster",\n'
            '    "Address": "456 Oak Avenue",\n'
            '    "Policy #": "P987654321"\n'
            '  },\n'
            '  "Assignment Information": {\n'
            '    "Date of Loss/Occurrence": "01/15/2024",\n'
            '    "Cause of loss": "Wind",\n'
            '    "Facts of Loss": "Severe storm caused roof damage.",\n'
            '    "Loss Description": "Damaged shingles and gutters.",\n'
            '    "Residence Occupied During Loss": "Yes",\n'
            '    "Was Someone home at time of damage": "Yes",\n'
            '    "Repair or Mitigation Progress": "Repairs underway",\n'
            '    "Type": "Structural",\n'
            '    "Inspection type": "Initial",\n'
            '    "Wind": true,\n'
            '    "Structural": false,\n'
            '    "Hail": false,\n'
            '    "Foundation": false,\n'
            '    "Other - provide details": null,\n'
            '    "Additional details/Special Instructions": "Inspect foundation as well.",\n'
            '    "Attachments": ["photo1.jpg", "report.pdf"]\n'
            '  }\n'
            '}\n'
        )
        return prompt

    def validate_data(self, data: Dict[str, Any]) -> bool:
        """
        Validates the extracted data against predefined schemas and rules.

        :param data: The extracted data dictionary.
        :return: True if data is valid, False otherwise.
        """
        required_fields = {
            "Requesting Party": ["Insurance Company", "Handler", "Carrier Claim Number"],
            "Insured Information": ["Name", "Contact #", "Loss Address"],
            "Adjuster Information": ["Adjuster Name", "Adjuster Phone Number", "Adjuster Email"],
            "Assignment Information": ["Date of Loss/Occurrence", "Cause of loss", "Loss Description"]
        }

        for section, fields in required_fields.items():
            for field in fields:
                if field not in data.get(section, {}) or not data[section][field]:
                    logging.warning(f"Validation failed: Missing or empty field '{field}' in section '{section}'.")
                    return False

        # Additional validation rules can be added here (e.g., date formats, phone number formats)
        # Example: Validate date format (mm/dd/yyyy)
        date = data["Assignment Information"]["Date of Loss/Occurrence"]
        if not re.match(r'\d{2}/\d{2}/\d{4}', date):
            logging.warning(f"Validation failed: Invalid date format '{date}'. Expected mm/dd/yyyy.")
            return False

        logging.info("Data validation successful.")
        return True

    def score_confidence(self, data: Dict[str, Any], raw_email: str) -> float:
        """
        Assigns a confidence score to the extracted data based on validation and other heuristics.

        :param data: The extracted data dictionary.
        :param raw_email: The raw email content.
        :return: A float representing the confidence score (0.0 to 1.0).
        """
        score = 1.0  # Start with maximum confidence

        # Deduct confidence for missing optional fields
        optional_fields = [
            "Public Adjuster",
            "Is the insured an Owner or a Tenant of the loss location?",
            "Job Title",
            "Policy #",
            "Wind",
            "Structural",
            "Hail",
            "Foundation",
            "Other - provide details",
            "Additional details/Special Instructions",
            "Attachments"
        ]

        missing_optional = 0
        for section in ["Requesting Party", "Insured Information", "Adjuster Information", "Assignment Information"]:
            for field in optional_fields:
                if field in data.get(section, {}) and not data[section][field]:
                    missing_optional += 1

        # Example heuristic: Deduct 0.02 for each missing optional field
        score -= 0.02 * missing_optional

        # Further deductions can be based on validation failures, inconsistencies, etc.
        # For example, if validation failed:
        # if not self.validate_data(data):
        #     score -= 0.5

        # Ensure score is within bounds
        score = max(0.0, min(score, 1.0))
        logging.info(f"Confidence score assigned: {score}")
        return score

    def parse_email(self, raw_email: bytes) -> Dict[str, Any]:
        """
        Parses a raw email and extracts relevant data fields with multi-layered verification.

        :param raw_email: The raw email content in bytes.
        :return: A dictionary containing extracted data fields and metadata.
        """
        try:
            # Parse the email content
            email_message = BytesParser(policy=policy.default).parsebytes(raw_email)
            logging.info(f"Parsed email from: {email_message['From']}")

            # Extract email body
            if email_message.is_multipart():
                # Get the plain text part
                for part in email_message.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get_content_disposition())
                    if content_type == 'text/plain' and 'attachment' not in content_disposition:
                        body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8')
                        break
                else:
                    body = ""
            else:
                body = email_message.get_payload(decode=True).decode(email_message.get_content_charset() or 'utf-8')

            # Use LLM to extract data
            extracted_data = self.extract_with_llm(body)

            # Automated Validation
            is_valid = self.validate_data(extracted_data)

            # Confidence Scoring
            confidence_score = self.score_confidence(extracted_data, body)

            # Determine if human review is needed
            needs_human_review = False
            if not is_valid or confidence_score < 0.85:
                needs_human_review = True
                logging.info("Data flagged for human review due to validation failure or low confidence.")

            # Prepare final output
            final_output = {
                "extracted_data": extracted_data,
                "validation": {
                    "is_valid": is_valid
                },
                "confidence_score": confidence_score,
                "needs_human_review": needs_human_review
            }

            return final_output

        except Exception as e:
            logging.error(f"Failed to parse email: {e}")
            return {}

    def parse_multiple_emails(self, raw_emails: List[bytes]) -> List[Dict[str, Any]]:
        """
        Parses multiple raw emails.

        :param raw_emails: A list of raw email contents in bytes.
        :return: A list of dictionaries containing extracted data fields and metadata.
        """
        parsed_data = []
        for raw_email in raw_emails:
            try:
                data = self.parse_email(raw_email)
                parsed_data.append(data)
            except Exception as e:
                logging.error(f"Failed to parse email: {e}")
        return parsed_data

if __name__ == "__main__":
    # Example usage
    parser = EmailParsingModule()

    # Path to an example email file (for testing purposes)
    example_email_path = Path('../examples/sample_email.eml')

    if example_email_path.exists():
        with open(example_email_path, 'rb') as f:
            raw_email = f.read()

        parsed_data = parser.parse_email(raw_email)
        print(json.dumps(parsed_data, indent=2))
    else:
        logging.error(f"Example email file not found at {example_email_path}")
