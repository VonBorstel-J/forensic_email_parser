# src/parsers/local_llm_parser.py

import logging
import json
from typing import Dict, Any

import requests

from .base_parser import BaseParser
from utils.config import Config


class LocalLLMParser(BaseParser):
    """
    An LLM-based parser that uses a locally hosted LLM to extract data from forensic engineering emails.
    """

    def __init__(self):
        self.api_endpoint = Config.LOCAL_LLM_API_ENDPOINT  # e.g., "http://localhost:8000/v1/chat/completions"
        self.logger = logging.getLogger(self.__class__.__name__)

    def parse(self, email_content: str) -> Dict[str, Any]:
        """
        Parse the email content using a local LLM to extract relevant data fields.

        :param email_content: The raw content of the email.
        :return: A dictionary containing the extracted data.
        """
        preprocessed_content = self.preprocess_email(email_content)
        extracted_data = {}

        prompt = self.construct_prompt(preprocessed_content)

        payload = {
            "model": "gpt-4",  # Adjust based on the local model's name
            "messages": [
                {"role": "system", "content": "You are an assistant that extracts structured data from forensic engineering emails."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 500
        }

        try:
            response = requests.post(self.api_endpoint, json=payload, timeout=30)
            response.raise_for_status()
            ai_response = response.json().get('choices', [{}])[0].get('message', {}).get('content', '')
            self.logger.debug(f"AI response: {ai_response}")

            extracted_data = self.parse_ai_response(ai_response)

        except requests.exceptions.RequestException as e:
            self.logger.error(f"Local LLM API request failed: {str(e)}")
            raise

        return extracted_data

    def construct_prompt(self, email_content: str) -> str:
        """
        Construct a prompt for the local LLM based on the email content.

        :param email_content: Preprocessed email content.
        :return: AI prompt string.
        """
        prompt = (
            "Extract the following fields from the given forensic engineering email and provide the data in JSON format. "
            "Ensure that all fields are present and correctly populated.\n\n"
            "Fields to extract:\n"
            "- Requesting Party Insurance Company\n"
            "- Handler\n"
            "- Carrier Claim Number\n"
            "- Insured Information:\n"
            "  - Name\n"
            "  - Contact #\n"
            "  - Loss Address\n"
            "  - Public Adjuster\n"
            "  - Ownership (Owner or Tenant)\n"
            "- Adjuster Information:\n"
            "  - Adjuster Name\n"
            "  - Adjuster Phone Number\n"
            "  - Adjuster Email\n"
            "  - Job Title\n"
            "  - Address\n"
            "  - Policy Number\n"
            "- Assignment Information:\n"
            "  - Date of Loss/Occurrence\n"
            "  - Cause of loss\n"
            "  - Facts of Loss\n"
            "  - Loss Description\n"
            "  - Residence Occupied During Loss\n"
            "  - Someone home at time of damage\n"
            "  - Repair or Mitigation Progress\n"
            "  - Type\n"
            "  - Inspection type\n"
            "- Assignment Type:\n"
            "  - Wind (True/False)\n"
            "  - Structural (True/False)\n"
            "  - Hail (True/False)\n"
            "  - Foundation (True/False)\n"
            "  - Other (True/False)\n"
            "- Additional details/Special Instructions\n"
            "- Attachments\n\n"
            "Email Content:\n"
            f"{email_content}\n\n"
            "Provide the extracted data in the following JSON format:\n"
            "{\n"
            '  "Requesting Party Insurance Company": "",\n'
            '  "Handler": "",\n'
            '  "Carrier Claim Number": "",\n'
            '  "Insured Information": {\n'
            '    "Name": "",\n'
            '    "Contact #": "",\n'
            '    "Loss Address": "",\n'
            '    "Public Adjuster": "",\n'
            '    "Ownership": ""\n'
            '  },\n'
            '  "Adjuster Information": {\n'
            '    "Adjuster Name": "",\n'
            '    "Adjuster Phone Number": "",\n'
            '    "Adjuster Email": "",\n'
            '    "Job Title": "",\n'
            '    "Address": "",\n'
            '    "Policy Number": ""\n'
            '  },\n'
            '  "Assignment Information": {\n'
            '    "Date of Loss/Occurrence": "",\n'
            '    "Cause of loss": "",\n'
            '    "Facts of Loss": "",\n'
            '    "Loss Description": "",\n'
            '    "Residence Occupied During Loss": "",\n'
            '    "Someone home at time of damage": "",\n'
            '    "Repair or Mitigation Progress": "",\n'
            '    "Type": "",\n'
            '    "Inspection type": ""\n'
            '  },\n'
            '  "Assignment Type": {\n'
            '    "Wind": false,\n'
            '    "Structural": false,\n'
            '    "Hail": false,\n'
            '    "Foundation": false,\n'
            '    "Other": false\n'
            '  },\n'
            '  "Additional details/Special Instructions": "",\n'
            '  "Attachments": ""\n'
            "}\n"
        )
        return prompt

    def parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """
        Parse the local LLM model's response to extract the validated data.

        :param ai_response: The raw response string from the local LLM model.
        :return: Validated data dictionary.
        """
        try:
            # Extract JSON part from the response
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            json_str = ai_response[json_start:json_end]
            validated_data = json.loads(json_str)
            self.logger.info("Local LLM-assisted validation successful.")
            return validated_data
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse local LLM response as JSON.")
            raise
