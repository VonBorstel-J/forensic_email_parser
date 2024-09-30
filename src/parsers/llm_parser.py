# src/parsers/llm_parser.py

import logging
import json
from typing import Dict, Any
import openai
from openai import OpenAIError, RateLimitError, APIError, Timeout
from utils.config import Config
from .base_parser import BaseParser


class LLMParser(BaseParser):
    """An LLM-based parser that uses OpenAI's GPT models to extract data from unstructured emails."""

    def __init__(self):
        super().__init__()
        self.api_key = Config.OPENAI_API_KEY
        openai.api_key = self.api_key
        self.logger.info("LLMParser initialized with OpenAI API.")

    def parse(self, email_content: str) -> Dict[str, Any]:
        """Parse the email content using an LLM to extract relevant data fields."""
        try:
            self.logger.info("Starting LLM-based parsing.")
            preprocessed_content = self.preprocess_email(email_content)
            prompt = self.construct_prompt(preprocessed_content)

            response = self.call_openai_api(prompt)
            ai_response = response.choices[0].message["content"]
            self.logger.debug(f"AI response: {ai_response}")

            extracted_data = self.parse_ai_response(ai_response)
            self.logger.info("LLM-based parsing completed successfully.")
            return extracted_data

        except OpenAIError as e:
            self.logger.error("OpenAI API error during LLM parsing: %s", str(e))
            raise
        except Exception as e:
            self.logger.exception("Unexpected error during LLM parsing.")
            raise

    def call_openai_api(self, prompt: str) -> Any:
        """Call the OpenAI API with retries for transient errors."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.debug(f"Calling OpenAI API, attempt {attempt + 1}.")
                response = openai.ChatCompletion.create(
                    model="gpt-4",
                    messages=[
                        {
                            "role": "system",
                            "content": "You are an assistant that extracts structured data from forensic engineering emails.",
                        },
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.2,
                    max_tokens=500,
                )
                self.logger.debug("OpenAI API call successful.")
                return response
            except (RateLimitError, APIError, Timeout) as e:
                self.logger.warning(
                    "OpenAI API error on attempt %d: %s", attempt + 1, str(e)
                )
                if attempt < max_retries - 1:
                    self.logger.info("Retrying OpenAI API request...")
                    continue
                else:
                    self.logger.error("Max retries reached for OpenAI API.")
                    raise
            except Exception as e:
                self.logger.exception("Unexpected error during OpenAI API call.")
                raise

    def construct_prompt(self, email_content: str) -> str:
        """Construct a prompt for the AI model based on the email content."""
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
        self.logger.debug("Constructed prompt for OpenAI API.")
        return prompt

    def parse_ai_response(self, ai_response: str) -> Dict[str, Any]:
        """Parse the AI model's response to extract the validated data."""
        try:
            self.logger.debug("Parsing AI response.")
            json_start = ai_response.find("{")
            json_end = ai_response.rfind("}") + 1
            if json_start == -1 or json_end == -1:
                self.logger.error("JSON not found in AI response.")
                raise ValueError("AI response does not contain valid JSON.")
            json_str = ai_response[json_start:json_end]
            validated_data = json.loads(json_str)
            self.logger.info("LLM-assisted validation successful.")
            return validated_data
        except json.JSONDecodeError as e:
            self.logger.error("Failed to parse AI response as JSON: %s", str(e))
            raise
        except Exception as e:
            self.logger.exception("Unexpected error while parsing AI response.")
            raise
