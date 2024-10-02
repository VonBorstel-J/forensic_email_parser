# src/quickbase_integration.py

import logging
import requests
from typing import Dict, Any
from utils.config import Config
from data_validation import AssignmentSchema
import json
from logging.handlers import RotatingFileHandler


class QuickbaseIntegrationError(Exception):
    """Custom exception for Quickbase integration errors."""

    pass


class QuickbaseIntegrator:
    """Handles integration with QuickBase API."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.setup_logger()
        self.api_url = Config.QUICKBASE_API_URL
        self.user_token = Config.QUICKBASE_USER_TOKEN
        self.realm_hostname = Config.QUICKBASE_REALM_HOSTNAME
        self.table_id = Config.QUICKBASE_TABLE_ID
        self.headers = {
            "QB-Realm-Hostname": self.realm_hostname,
            "User-Agent": "forensic_email_parser/1.0",
            "Authorization": f"QB-USER-TOKEN {self.user_token}",
            "Content-Type": "application/json",
        }
        self.logger.info("QuickbaseIntegrator initialized with provided configuration.")

    def setup_logger(self):
        """Sets up a rotating file handler for logging."""
        handler = RotatingFileHandler(
            Config.LOG_FILE, maxBytes=5 * 1024 * 1024, backupCount=5
        )
        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)  # Set to DEBUG for detailed logs

    def map_data_to_quickbase(self, data: AssignmentSchema) -> Dict[str, Any]:
        """
        Maps the validated AssignmentSchema data to QuickBase fields.
        Adjust the field mappings based on your QuickBase table schema.
        """
        try:
            self.logger.debug("Mapping data to QuickBase fields.")
            mapped_data = {
                "6": {
                    "value": data.requesting_party.insurance_company
                },  # Insurance Company
                "7": {"value": data.requesting_party.handler},  # Handler
                "8": {
                    "value": data.requesting_party.carrier_claim_number
                },  # Carrier Claim Number
                "9": {"value": data.insured_information.name},  # Insured Name
                "10": {
                    "value": data.insured_information.contact_number
                },  # Contact Number
                "11": {"value": data.insured_information.loss_address},  # Loss Address
                "12": {
                    "value": data.insured_information.public_adjuster
                },  # Public Adjuster
                "13": {
                    "value": data.insured_information.ownership_status
                },  # Ownership Status
                "14": {
                    "value": data.adjuster_information.adjuster_name
                },  # Adjuster Name
                "15": {
                    "value": data.adjuster_information.adjuster_phone_number
                },  # Adjuster Phone
                "16": {
                    "value": data.adjuster_information.adjuster_email
                },  # Adjuster Email
                "17": {"value": data.adjuster_information.job_title},  # Job Title
                "18": {"value": data.adjuster_information.address},  # Adjuster Address
                "19": {
                    "value": data.adjuster_information.policy_number
                },  # Policy Number
                "20": {
                    "value": data.assignment_information.date_of_loss.isoformat()
                },  # Date of Loss
                "21": {
                    "value": data.assignment_information.cause_of_loss
                },  # Cause of Loss
                "22": {
                    "value": data.assignment_information.facts_of_loss
                },  # Facts of Loss
                "23": {
                    "value": data.assignment_information.loss_description
                },  # Loss Description
                "24": {
                    "value": data.assignment_information.residence_occupied_during_loss
                },  # Residence Occupied
                "25": {
                    "value": data.assignment_information.was_someone_home_at_time_of_damage
                },  # Someone Home
                "26": {
                    "value": data.assignment_information.repair_or_mitigation_progress
                },  # Repair Progress
                "27": {"value": data.assignment_information.type},  # Type
                "28": {
                    "value": data.assignment_information.inspection_type
                },  # Inspection Type
                "29": {
                    "value": ", ".join(
                        [
                            atype.value
                            for atype in data.assignment_details.assignment_type
                        ]
                    )
                },  # Assignment Types
                "30": {
                    "value": data.assignment_details.other_details or ""
                },  # Other Details
                "31": {
                    "value": data.assignment_details.additional_details or ""
                },  # Additional Details
                "32": {
                    "value": (
                        ", ".join(data.assignment_details.attachments)
                        if data.assignment_details.attachments
                        else ""
                    )
                },  # Attachments
            }
            self.logger.debug(f"Mapped data: {json.dumps(mapped_data, indent=4)}")
            return mapped_data
        except Exception as e:
            self.logger.exception("Error during data mapping to QuickBase fields.")
            raise QuickbaseIntegrationError(f"Data mapping failed: {str(e)}") from e

    def insert_record(self, data: AssignmentSchema) -> Dict[str, Any]:
        """
        Inserts a validated record into QuickBase.
        """
        try:
            self.logger.info("Preparing to insert record into QuickBase.")
            mapped_data = self.map_data_to_quickbase(data)
            payload = {"to": self.table_id, "data": [{"fields": mapped_data}]}
            self.logger.debug(
                f"Payload for QuickBase API: {json.dumps(payload, indent=4)}"
            )
            self.logger.info("Sending data to QuickBase API.")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json=payload,
                timeout=30,  # Timeout after 30 seconds
            )
            response.raise_for_status()  # Raise HTTPError for bad responses
            result = response.json()
            self.logger.info(
                f"Successfully inserted record into QuickBase: {json.dumps(result, indent=4)}"
            )
            return result
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(
                f"HTTP error occurred: {http_err} - Response: {response.text}"
            )
            raise QuickbaseIntegrationError(f"HTTP error: {http_err}") from http_err
        except requests.exceptions.Timeout:
            self.logger.error("Request to QuickBase API timed out.")
            raise QuickbaseIntegrationError("QuickBase API request timed out.")
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request exception: {req_err}")
            raise QuickbaseIntegrationError(f"Request error: {req_err}") from req_err
        except Exception as e:
            self.logger.exception("Unexpected error during QuickBase record insertion.")
            raise QuickbaseIntegrationError(f"Insertion failed: {str(e)}") from e

    def verify_record_insertion(self, record_id: str) -> bool:
        """
        Verifies that the record has been successfully inserted into QuickBase.
        """
        try:
            self.logger.info(f"Verifying insertion of record ID: {record_id}")
            # Construct the query to fetch the record
            query_url = f"{self.api_url}/{record_id}"
            self.logger.debug(f"Query URL for verification: {query_url}")
            response = requests.get(query_url, headers=self.headers, timeout=30)
            response.raise_for_status()
            record = response.json()
            self.logger.info(
                f"Record verification successful: {json.dumps(record, indent=4)}"
            )
            return True
        except requests.exceptions.HTTPError as http_err:
            self.logger.error(
                f"HTTP error during verification: {http_err} - Response: {response.text}"
            )
            return False
        except requests.exceptions.Timeout:
            self.logger.error("Verification request to QuickBase API timed out.")
            return False
        except requests.exceptions.RequestException as req_err:
            self.logger.error(f"Request exception during verification: {req_err}")
            return False
        except Exception as e:
            self.logger.exception(f"Unexpected error during record verification: {e}")
            return False


# Example usage
if __name__ == "__main__":
    import json
    from data_validation import AssignmentSchema, AssignmentTypeEnum
    from datetime import date

    # Sample validated data (replace with actual validated AssignmentSchema instance)
    sample_validated_data = AssignmentSchema(
        requesting_party={
            "Insurance Company": "ABC Insurance",
            "Handler": "John Doe",
            "Carrier Claim Number": "CLM123456",
        },
        insured_information={
            "Name": "Jane Smith",
            "Contact #": "+12345678901",
            "Loss Address": "123 Main St, Anytown, USA",
            "Public Adjuster": "Adjuster Inc.",
            "Is the insured an Owner or a Tenant of the loss location?": "Owner",
        },
        adjuster_information={
            "Adjuster Name": "Mike Johnson",
            "Adjuster Phone Number": "+10987654321",
            "Adjuster Email": "mike.johnson@example.com",
            "Job Title": "Senior Adjuster",
            "Address": "456 Elm St, Othertown, USA",
            "Policy #": "POL789012",
        },
        assignment_information={
            "Date of Loss/Occurrence": date(2023, 8, 15),
            "Cause of loss": "Windstorm",
            "Facts of Loss": "Tree fell on roof causing extensive damage.",
            "Loss Description": "Roof damaged, windows broken.",
            "Residence Occupied During Loss": "Yes",
            "Was Someone home at time of damage": "No",
            "Repair or Mitigation Progress": "Initial assessment completed.",
            "Type": "Residential",
            "Inspection type": "Full Inspection",
        },
        assignment_details={
            "assignment_type": [AssignmentTypeEnum.WIND, AssignmentTypeEnum.STRUCTURAL],
            "other_details": "N/A",
            "additional_details": "Please prioritize the roof repair.",
            "attachments": ["photo1.jpg", "report.pdf"],
        },
    )

    integrator = QuickbaseIntegrator()
    try:
        result = integrator.insert_record(sample_validated_data)
        print("Record inserted successfully:", json.dumps(result, indent=4))
        # Assuming the response contains the record ID, adjust according to actual API response
        record_id = result.get("data", [{}])[0].get("id")
        if record_id:
            verification = integrator.verify_record_insertion(record_id)
            if verification:
                print(f"Record ID {record_id} verified successfully in QuickBase.")
            else:
                print(f"Failed to verify Record ID {record_id} in QuickBase.")
        else:
            print("Record ID not found in the response.")
    except QuickbaseIntegrationError as e:
        print(f"Failed to insert record: {e}")
