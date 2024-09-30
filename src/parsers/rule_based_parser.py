# src/parsers/rule_based_parser.py

from mailparser import parse_from_string
from .base_parser import BaseParser
from typing import Dict, Any
import re

class RuleBasedParser(BaseParser):
    """
    A rule-based parser that extracts data from well-structured emails using regex patterns.
    """

    def parse(self, email_content: str) -> Dict[str, Any]:
        """
        Parse the email content using regex and mail-parser to extract relevant data fields.

        :param email_content: The raw content of the email.
        :return: A dictionary containing the extracted data.
        """
        preprocessed_content = self.preprocess_email(email_content)
        extracted_data = {}

        # Use mail-parser to parse the email
        mail = parse_from_string(preprocessed_content)

        # Extract headers
        extracted_data['From'] = mail.from_
        extracted_data['To'] = mail.to
        extracted_data['Subject'] = mail.subject
        extracted_data['Date'] = mail.date

        # Extract body content
        body = mail.body
        extracted_data['Body'] = body

        # Define regex patterns for specific fields
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
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                if "Assignment Type" in field:
                    # Convert checkbox to boolean
                    extracted_data[field] = bool(match.group(1))
                else:
                    extracted_data[field] = match.group(1).strip()
            else:
                if "Ownership" in field:
                    # Handle Owner/Tenant
                    ownership_match = re.search(r"Owner|Tenant", body, re.IGNORECASE)
                    extracted_data[field] = ownership_match.group(0).strip() if ownership_match else None
                else:
                    extracted_data[field] = None

        # Process attachments if any
        extracted_data['Attachments'] = [attachment.filename for attachment in mail.attachments] if mail.attachments else []

        return extracted_data
