# src/parsers/local_llm_parser.py

import logging
import json
from typing import Dict, Any
import requests
from requests.exceptions import RequestException, HTTPError, Timeout, ConnectionError
from .base_parser import BaseParser
from utils.config import Config


class LocalLLMParser(BaseParser):
    """An LLM-based parser that uses a locally hosted LLM to extract data from forensic engineering emails."""

    def __init__(self):
        super().__init__()
        self.api_endpoint = (
            Config.LOCAL_LLM_API_ENDPOINT
        )  # e.g., "http://localhost:8000/v1/chat/completions"
        self.logger.info(
            f"LocalLLMParser initialized with endpoint: {self.api_endpoint}"
        )

    def parse(self, email_content: str) -> Dict[str, Any]:
        """Parse the email content using a local LLM to extract relevant data fields."""
        try:
            self.logger.info("Starting Local LLM-based parsing.")
            preprocessed_content = self.preprocess_email(email_content)
            prompt = self.construct_prompt(preprocessed_content)
            ai_response = self.call_local_llm_api(prompt)
            self.logger.debug(f"AI response: {ai_response}")

            extracted_data = self.parse_ai_response(ai_response)
            self.logger.info("Local LLM-based parsing completed successfully.")
            return extracted_data

        except Exception as e:
            self.logger.exception("Error during local LLM parsing.")
            raise

    def call_local_llm_api(self, prompt: str) -> str:
        """Call the local LLM API with error handling and retries."""
        max_retries = 3
        payload = {
            "model": "gpt-4",  # Adjust based on the local model's name
            "messages": [
                {
                    "role": "system",
                    "content": "You are an assistant that extracts structured data from forensic engineering emails.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
            "max_tokens": 500,
        }

        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Calling local LLM API, attempt {attempt + 1}.")
                response = requests.post(self.api_endpoint, json=payload, timeout=30)
                response.raise_for_status()
                json_response = response.json()
                ai_response = (
                    json_response.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                )
                if not ai_response:
                    self.logger.error("Empty response from local LLM API.")
                    raise ValueError("Received empty response from local LLM API.")
                self.logger.debug("Local LLM API call successful.")
                return ai_response

            except (HTTPError, ConnectionError, Timeout) as e:
                self.logger.warning(
                    "Local LLM API error on attempt %d: %s", attempt + 1, str(e)
                )
                if attempt < max_retries - 1:
                    self.logger.info("Retrying local LLM API request...")
                    continue
                else:
                    self.logger.error("Max retries reached for local LLM API.")
                    raise
            except ValueError as e:
                self.logger.error("Invalid response from local LLM API: %s", str(e))
                raise
            except RequestException as e:
                self.logger.error(
                    "RequestException during local LLM API call: %s", str(e)
                )
                raise
            except Exception as e:
                self.logger.exception("Unexpected error during local LLM API call.")
                raise

    def construct_prompt(self, email_content: str) -> str:
        """Construct a prompt for the local LLM based on the email content."""
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
            "Provide the extracted data in JSON format."
        )
        self.logger.debug("Constructed prompt for Local LLM API.")
        return prompt

    def parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the local LLM model's response to extract the validated data."""
        try:
            self.logger.debug("Parsing Local LLM response.")
            json_start = ai_response.find("{")
            json_end = ai_response.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                self.logger.error("JSON not found in Local LLM response.")
                raise ValueError("Local LLM response does not contain valid JSON.")
            json_str = ai_response[json_start:json_end]
            validated_data = json.loads(json_str)
            self.logger.info("Local LLM-assisted validation successful.")
            return validated_data
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse Local LLM response as JSON: %s", str(e))
            raise
        except Exception as e:
            self.logger.exception("Unexpected error while parsing Local LLM response.")
            raise
