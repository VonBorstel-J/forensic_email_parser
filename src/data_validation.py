# src/data_validation.py

from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr, validator
from enum import Enum
from datetime import date
import logging


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

    @validator("contact_number")
    def validate_contact_number(cls, v):
        import re

        pattern = re.compile(
            r"^\+?1?\d{9,15}$"
        )  # Simple international phone number regex
        if not pattern.match(v):
            raise ValueError("Invalid contact number format.")
        return v


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
    """Validates extracted data against the Assignment Schema."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.logger.info("DataValidator initialized.")

    def validate(self, data: Dict[str, Any]) -> AssignmentSchema:
        """Validates the data and returns an AssignmentSchema instance."""
        try:
            self.logger.info("Starting data validation.")
            validated_data = AssignmentSchema(**data)
            self.logger.info("Data validation successful.")
            return validated_data
        except Exception as e:
            self.logger.error("Data validation failed: %s", str(e))
            raise DataValidationError(str(e))


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
        "Check the box of applicable assignment type": ["Wind", "Structural"],
        "Other - provide details": "N/A",
        "Additional details/Special Instructions": "Please prioritize the roof repair.",
        "Attachment(s)": ["photo1.jpg", "report.pdf"],
    }

    validator = DataValidator()
    try:
        validated_assignment = validator.validate(sample_data)
        print("Validation successful.")
        print(validated_assignment.json(by_alias=True, indent=4))
    except DataValidationError as e:
        print(f"Validation failed: {e}")
