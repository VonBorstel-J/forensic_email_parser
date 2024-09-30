# src/parsers/rule_based_parser.py

import re
from typing import Dict, Any

from .base_parser import BaseParser


class RuleBasedParser(BaseParser):
    """
    A rule-based parser that extracts data from well-structured emails using regex patterns.
    """

    def parse(self, email_content: str) -> Dict[str, Any]:
        """
        Parse the email content using regex to extract relevant data fields.

        :param email_content: The raw content of the email.
        :return: A dictionary containing the extracted data.
        """
        preprocessed_content = self.preprocess_email(email_content)
        extracted_data = {}

        # Define regex patterns for each field
        patterns = {
            "Requesting Party Insurance Company": r"Requesting Party Insurance Company:\s*(.*)",
            "Handler": r"Handler:\s*(.*)",
            "Carrier Claim Number": r"Carrier Claim Number:\s*(.*)",
            "Insured Name": r"Name:\s*(.*)",
            "Insured Contact #": r"Contact #:\s*(.*)",
            "Loss Address": r"Loss Address:\s*(.*)",
            "Public Adjuster": r"Public Adjuster:\s*(.*)",
            "Ownership": r"Owner|Tenant",
            "Adjuster Name": r"Adjuster Name:\s*(.*)",
            "Adjuster Phone Number": r"Adjuster Phone Number:\s*(.*)",
            "Adjuster Email": r"Adjuster Email:\s*(.*)",
            "Job Title": r"Job Title:\s*(.*)",
            "Adjuster Address": r"Address:\s*(.*)",
            "Policy Number": r"Policy #:\s*(.*)",
            "Date of Loss/Occurrence": r"Date of Loss/Occurrence:\s*(.*)",
            "Cause of loss": r"Cause of loss:\s*(.*)",
            "Facts of Loss": r"Facts of Loss:\s*(.*)",
            "Loss Description": r"Loss Description:\s*(.*)",
            "Residence Occupied During Loss": r"Residence Occupied During Loss:\s*(.*)",
            "Someone home at time of damage": r"Someone home at time of damage:\s*(.*)",
            "Repair or Mitigation Progress": r"Repair or Mitigation Progress:\s*(.*)",
            "Type": r"Type:\s*(.*)",
            "Inspection type": r"Inspection type:\s*(.*)",
            "Assignment Type - Wind": r"Wind\s*\[\s*(x|X)?\s*\]",
            "Assignment Type - Structural": r"Structural\s*\[\s*(x|X)?\s*\]",
            "Assignment Type - Hail": r"Hail\s*\[\s*(x|X)?\s*\]",
            "Assignment Type - Foundation": r"Foundation\s*\[\s*(x|X)?\s*\]",
            "Assignment Type - Other": r"Other\s*\[\s*(x|X)?\s*\]",
            "Additional details/Special Instructions": r"Additional details/Special Instructions:\s*(.*)",
            "Attachments": r"Attachment\(s\):\s*(.*)"
        }

        for field, pattern in patterns.items():
            match = re.search(pattern, preprocessed_content, re.IGNORECASE | re.DOTALL)
            if match:
                value = match.group(1).strip()
                # Handle boolean fields for assignment types
                if field.startswith("Assignment Type"):
                    extracted_data[field] = True if match.group(1).lower() == 'x' else False
                elif field == "Ownership":
                    extracted_data[field] = "Owner" if "Owner" in match.group(0) else "Tenant"
                else:
                    extracted_data[field] = value
            else:
                # If the field is "Ownership" and not matched yet, set default
                if field == "Ownership":
                    extracted_data[field] = "Unknown"

        return extracted_data
