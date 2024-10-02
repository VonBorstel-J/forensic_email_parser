# src/data_validation.py

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, EmailStr, validator, root_validator
from enum import Enum
from datetime import date
import logging
import os
import openai
import json
import re

# Configure logging with enhanced formatting and security considerations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler()],
)


class AssignmentTypeEnum(str, Enum):
    WIND = "Wind"
    STRUCTURAL = "Structural"
    HAIL = "Hail"
    FOUNDATION = "Foundation"
    OTHER = "Other"


class RequestingParty(BaseModel):
    insurance_company: str = Field(..., alias="Insurance Company")
    handler: str = Field(..., alias="Handler")
    carrier_claim_number: str = Field(..., alias="Carrier Claim Number")


class InsuredInformation(BaseModel):
    name: str = Field(..., alias="Name")
    contact_number: str = Field(..., alias="Contact #")
    loss_address: str = Field(..., alias="Loss Address")
    public_adjuster: str = Field(..., alias="Public Adjuster")
    ownership_status: str = Field(
        ..., alias="Is the insured an Owner or a Tenant of the loss location?"
    )
    landlord_contact: Optional[str] = Field(
        None, alias="Landlord Contact"  # Added for cross-field validation
    )

    @validator("contact_number")
    def validate_contact_number(cls, v):
        

        pattern = re.compile(
            r"^\+?1?\d{9,15}$"
        )  # Simple international phone number regex
        if not pattern.match(v):
            raise ValueError("Invalid contact number format.")
        return v

    @validator("ownership_status")
    def validate_ownership_status(cls, v):
        if v not in ["Owner", "Tenant"]:
            raise ValueError("Ownership status must be 'Owner' or 'Tenant'.")
        return v

    @root_validator
    def check_tenant_fields(cls, values):
        ownership_status = values.get("ownership_status")
        landlord_contact = values.get("landlord_contact")
        if ownership_status == "Tenant" and not landlord_contact:
            raise ValueError(
                "Landlord contact is required when ownership status is 'Tenant'."
            )
        return values


class AdjusterInformation(BaseModel):
    adjuster_name: str = Field(..., alias="Adjuster Name")
    adjuster_phone_number: str = Field(..., alias="Adjuster Phone Number")
    adjuster_email: EmailStr = Field(..., alias="Adjuster Email")
    job_title: str = Field(..., alias="Job Title")
    address: str = Field(..., alias="Address")
    policy_number: str = Field(..., alias="Policy #")


class AssignmentInformation(BaseModel):
    date_of_loss: date = Field(..., alias="Date of Loss/Occurrence")
    cause_of_loss: str = Field(..., alias="Cause of loss")
    facts_of_loss: str = Field(..., alias="Facts of Loss")
    loss_description: str = Field(..., alias="Loss Description")
    residence_occupied_during_loss: str = Field(
        ..., alias="Residence Occupied During Loss"
    )
    was_someone_home_at_time_of_damage: str = Field(
        ..., alias="Was Someone home at time of damage"
    )
    repair_or_mitigation_progress: str = Field(
        ..., alias="Repair or Mitigation Progress"
    )
    type: str = Field(..., alias="Type")
    inspection_type: str = Field(..., alias="Inspection type")

    @validator("date_of_loss")
    def validate_date_of_loss(cls, v):
        if v > date.today():
            raise ValueError("Date of loss cannot be in the future.")
        return v


class AssignmentDetails(BaseModel):
    assignment_type: List[AssignmentTypeEnum] = Field(
        ..., alias="Check the box of applicable assignment type"
    )
    other_details: Optional[str] = Field(None, alias="Other - provide details")
    additional_details: Optional[str] = Field(
        None, alias="Additional details/Special Instructions"
    )
    attachments: Optional[List[str]] = Field(None, alias="Attachment(s)")


class AssignmentSchema(BaseModel):
    requesting_party: RequestingParty = Field(..., alias="Requesting Party")
    insured_information: InsuredInformation = Field(..., alias="Insured Information")
    adjuster_information: AdjusterInformation = Field(..., alias="Adjuster Information")
    assignment_information: AssignmentInformation = Field(
        ..., alias="Assignment Information"
    )
    assignment_details: AssignmentDetails = Field(..., alias="Assignment Details")

    class Config:
        allow_population_by_field_name = True
        anystr_strip_whitespace = True


class DataValidationError(Exception):
    """Custom exception for data validation errors."""

    pass


class DataValidator:
    """
    Class for validating data using rule-based and AI-assisted methods.
    """

    def __init__(self, request_id: Optional[str] = None):
        """
        Initializes the DataValidator with optional request context.
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        if request_id:
            self.logger = logging.LoggerAdapter(self.logger, {"request_id": request_id})
        self.logger.info("DataValidator initialized.")
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        if not self.openai_api_key:
            self.logger.warning(
                "OpenAI API key not found. AI-assisted validation will be disabled."
            )
        else:
            openai.api_key = self.openai_api_key

    def validate(self, data: Dict[str, Any]) -> AssignmentSchema:
        """
        Validates the input data and returns an AssignmentSchema instance.
        """
        try:
            self.logger.info("Starting rule-based data validation.")
            validated_data = AssignmentSchema(**data)
            self.logger.info("Rule-based data validation successful.")
            # Optionally perform AI-assisted validation
            ai_validated_data = self.ai_assisted_validation(data)
            if ai_validated_data != data:
                # Re-validate with the AI-assisted data
                self.logger.info("Starting re-validation with AI-assisted data.")
                validated_data = AssignmentSchema(**ai_validated_data)
                self.logger.info("Re-validation with AI-assisted data successful.")
            return validated_data
        except DataValidationError as e:
            self.logger.error(f"Data validation failed: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error during validation: {e}")
            raise DataValidationError(
                "An unexpected error occurred during validation."
            ) from e

    def ai_assisted_validation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Performs AI-assisted validation using OpenAI's GPT-4.
        """
        if not self.openai_api_key:
            self.logger.warning(
                "AI-assisted validation skipped due to missing API key."
            )
            return data  # Fallback to rule-based validation

        try:
            self.logger.info("Starting AI-assisted validation.")
            prompt = self.construct_ai_prompt(data)
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a data validation assistant.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=500,
            )
            ai_response = response.choices[0].message["content"]
            self.logger.debug("AI response received.")
            ai_validated_data = self.parse_ai_response(ai_response)
            self.logger.info("AI-assisted validation successful.")
            return ai_validated_data
        except openai.error.OpenAIError as e:
            self.logger.error(f"AI validation failed due to OpenAI API error: {e}")
            return data  # Fallback to rule-based validation
        except json.JSONDecodeError as parse_exception:
            self.logger.error(
                f"AI validation failed due to JSON decoding error: {parse_exception}"
            )
            return data  # Fallback to rule-based validation
        except Exception as parse_exception:
            self.logger.error(f"AI validation failed: {parse_exception}")
            return data  # Fallback to rule-based validation

    def construct_ai_prompt(self, data: Dict[str, Any]) -> str:
        """
        Constructs a prompt for the AI validation with explicit instructions.
        """
        anonymized_data = self.anonymize_data(data)
        prompt = (
            "Please perform a detailed validation of the following data. "
            "Ensure all fields are correctly formatted, logically consistent, and comply with the following rules: "
            "1. Dates must not be in the future. "
            "2. Contact numbers must be valid international phone numbers. "
            "3. Email addresses must be valid. "
            "4. Ownership status must be either 'Owner' or 'Tenant'. "
            "5. If ownership status is 'Tenant', 'Landlord Contact' must be provided. "
            "Return the validated data in JSON format with any necessary corrections.\n\n"
            f"Data: {json.dumps(anonymized_data, indent=4)}\n\n"
            "Validated Data:"
        )
        return prompt

    def parse_ai_response(self, response: str) -> Dict[str, Any]:
        """
        Parses the AI's response and extracts the validated data.
        """
        try:
            start = response.find("{")
            end = response.rfind("}") + 1
            if start == -1 or end == -1:
                raise ValueError("No JSON object found in AI response.")
            json_str = response[start:end]
            ai_validated_data = json.loads(json_str)
            self.logger.debug("AI response parsed successfully.")
            return ai_validated_data
        except Exception as parse_exception:
            self.logger.error(f"Failed to parse AI response: {parse_exception}")
            raise DataValidationError(
                "AI response could not be parsed."
            ) from parse_exception

    def anonymize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Anonymizes sensitive data before sending to AI for validation.
        """
        anonymized = json.loads(json.dumps(data))  # Deep copy
        if "Insured Information" in anonymized:
            anonymized["Insured Information"]["Contact #"] = "REDACTED"
            if "Landlord Contact" in anonymized["Insured Information"]:
                anonymized["Insured Information"]["Landlord Contact"] = "REDACTED"
        if "Adjuster Information" in anonymized:
            anonymized["Adjuster Information"]["Adjuster Phone Number"] = "REDACTED"
            anonymized["Adjuster Information"]["Adjuster Email"] = "REDACTED"
        return anonymized


# Example usage
if __name__ == "__main__":
    import json

    # Sample data (replace with actual extracted data)
    sample_data = {
        "Requesting Party": {
            "Insurance Company": "ABC Insurance",
            "Handler": "John Doe",
            "Carrier Claim Number": "CLM123456",
        },
        "Insured Information": {
            "Name": "Jane Smith",
            "Contact #": "+12345678901",
            "Loss Address": "123 Main St, Anytown, USA",
            "Public Adjuster": "Adjuster Inc.",
            "Is the insured an Owner or a Tenant of the loss location?": "Owner",
            "Landlord Contact": "N/A",  # Included for cross-field validation
        },
        "Adjuster Information": {
            "Adjuster Name": "Mike Johnson",
            "Adjuster Phone Number": "+10987654321",
            "Adjuster Email": "mike.johnson@example.com",
            "Job Title": "Senior Adjuster",
            "Address": "456 Elm St, Othertown, USA",
            "Policy #": "POL789012",
        },
        "Assignment Information": {
            "Date of Loss/Occurrence": "2023-08-15",
            "Cause of loss": "Windstorm",
            "Facts of Loss": "Tree fell on roof causing extensive damage.",
            "Loss Description": "Roof damaged, windows broken.",
            "Residence Occupied During Loss": "Yes",
            "Was Someone home at time of damage": "No",
            "Repair or Mitigation Progress": "Initial assessment completed.",
            "Type": "Residential",
            "Inspection type": "Full Inspection",
        },
        "Assignment Details": {  # Nested under "Assignment Details"
            "Check the box of applicable assignment type": ["Wind", "Structural"],
            "Other - provide details": "N/A",
            "Additional details/Special Instructions": "Please prioritize the roof repair.",
            "Attachment(s)": ["photo1.jpg", "report.pdf"],
        },
    }

    # Initialize the DataValidator with an optional request ID for enhanced logging
    validator = DataValidator(request_id="REQ123456")

    try:
        validated_assignment = validator.validate(sample_data)
        print("Validation successful.")
        print(validated_assignment.json(by_alias=True, indent=4))
    except DataValidationError as e:
        print(f"Validation failed: {e}")
