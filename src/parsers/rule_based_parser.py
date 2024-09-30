# rule_based_parser.py

from mailparser import parse_from_string, MailParser
from .base_parser import BaseParser
from typing import Dict, Any
import re
import logging


class RuleBasedParser(BaseParser):
    """A rule-based parser that extracts data from well-structured emails using regex patterns."""

    def __init__(self):
        super().__init__()
        self.patterns = self.compile_patterns()

    def compile_patterns(self):
        patterns = {
            "Requesting Party Insurance Company": re.compile(
                r"Requesting Party Insurance Company:\s*(.*)", re.IGNORECASE
            ),
            "Handler": re.compile(r"Handler:\s*(.*)", re.IGNORECASE),
            "Carrier Claim Number": re.compile(
                r"Carrier Claim Number:\s*(.*)", re.IGNORECASE
            ),
            "Insured Name": re.compile(r"Name:\s*(.*)", re.IGNORECASE),
            "Insured Contact #": re.compile(r"Contact #:\s*(.*)", re.IGNORECASE),
            "Loss Address": re.compile(r"Loss Address:\s*(.*)", re.IGNORECASE),
            "Public Adjuster": re.compile(r"Public Adjuster:\s*(.*)", re.IGNORECASE),
            "Ownership": re.compile(r"Owner|Tenant", re.IGNORECASE),
            "Adjuster Name": re.compile(r"Adjuster Name:\s*(.*)", re.IGNORECASE),
            "Adjuster Phone Number": re.compile(
                r"Adjuster Phone Number:\s*(.*)", re.IGNORECASE
            ),
            "Adjuster Email": re.compile(r"Adjuster Email:\s*(.*)", re.IGNORECASE),
            "Job Title": re.compile(r"Job Title:\s*(.*)", re.IGNORECASE),
            "Adjuster Address": re.compile(r"Address:\s*(.*)", re.IGNORECASE),
            "Policy Number": re.compile(r"Policy #:\s*(.*)", re.IGNORECASE),
            "Date of Loss/Occurrence": re.compile(
                r"Date of Loss/Occurrence:\s*(.*)", re.IGNORECASE
            ),
            "Cause of loss": re.compile(r"Cause of loss:\s*(.*)", re.IGNORECASE),
            "Facts of Loss": re.compile(r"Facts of Loss:\s*(.*)", re.IGNORECASE),
            "Loss Description": re.compile(r"Loss Description:\s*(.*)", re.IGNORECASE),
            "Residence Occupied During Loss": re.compile(
                r"Residence Occupied During Loss:\s*(.*)", re.IGNORECASE
            ),
            "Someone home at time of damage": re.compile(
                r"Someone home at time of damage:\s*(.*)", re.IGNORECASE
            ),
            "Repair or Mitigation Progress": re.compile(
                r"Repair or Mitigation Progress:\s*(.*)", re.IGNORECASE
            ),
            "Type": re.compile(r"Type:\s*(.*)", re.IGNORECASE),
            "Inspection type": re.compile(r"Inspection type:\s*(.*)", re.IGNORECASE),
            "Assignment Type - Wind": re.compile(
                r"Wind\s*\[\s*(x|X)?\s*\]", re.IGNORECASE
            ),
            "Assignment Type - Structural": re.compile(
                r"Structural\s*\[\s*(x|X)?\s*\]", re.IGNORECASE
            ),
            "Assignment Type - Hail": re.compile(
                r"Hail\s*\[\s*(x|X)?\s*\]", re.IGNORECASE
            ),
            "Assignment Type - Foundation": re.compile(
                r"Foundation\s*\[\s*(x|X)?\s*\]", re.IGNORECASE
            ),
            "Assignment Type - Other": re.compile(
                r"Other\s*\[\s*(x|X)?\s*\]", re.IGNORECASE
            ),
            "Additional details/Special Instructions": re.compile(
                r"Additional details/Special Instructions:\s*(.*)", re.IGNORECASE
            ),
            "Attachments": re.compile(r"Attachment\(s\):\s*(.*)", re.IGNORECASE),
        }
        return patterns

    def parse(self, email_content: str) -> Dict[str, Any]:
        """Parse the email content using regex and mail-parser to extract relevant data fields."""
        try:
            preprocessed_content = self.preprocess_email(email_content)
            extracted_data = {}

            # Use mail-parser to parse the email
            mail = parse_from_string(preprocessed_content)

            # Extract headers
            extracted_data["From"] = mail.from_
            extracted_data["To"] = mail.to
            extracted_data["Subject"] = mail.subject
            extracted_data["Date"] = mail.date

            # Extract body content
            body = mail.body
            extracted_data["Body"] = body

            # Use compiled regex patterns
            for field, pattern in self.patterns.items():
                match = pattern.search(body)
                if match:
                    if "Assignment Type" in field:
                        # Convert checkbox to boolean
                        extracted_data[field] = bool(match.group(1))
                    else:
                        extracted_data[field] = match.group(1).strip()
                else:
                    self.logger.warning("Pattern not matched for field: %s", field)
                    extracted_data[field] = None

            # Process attachments if any
            extracted_data["Attachments"] = (
                [attachment["filename"] for attachment in mail.attachments_list]
                if mail.attachments_list
                else []
            )

            return extracted_data

        except MailParser.MailParserError as e:
            self.logger.error("MailParser error: %s", str(e))
            raise
        except re.error as e:
            self.logger.error("Regex error while parsing email: %s", str(e))
            raise
        except Exception as e:
            self.logger.exception("Unexpected error during rule-based parsing.")
            raise
