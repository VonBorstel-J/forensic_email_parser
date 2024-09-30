import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
import json
from src.email_parsing import EmailParsingModule

class TestEmailParsingModule(unittest.TestCase):
    def setUp(self):
        # Initialize the parser with the spaCy model and a mock LLM model
        self.parser = EmailParsingModule()
    
    @patch('src.email_parsing.spacy.load')
    def test_init_success(self, mock_spacy_load):
        # Mock successful spaCy model loading
        mock_nlp = MagicMock()
        mock_spacy_load.return_value = mock_nlp

        parser = EmailParsingModule(nlp_model='en_core_web_sm')
        mock_spacy_load.assert_called_with('en_core_web_sm')
        self.assertEqual(parser.nlp, mock_nlp)
    
    @patch('src.email_parsing.openai.ChatCompletion.create')
    def test_extract_with_llm_success(self, mock_openai_create):
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message={
                    'content': json.dumps({
                        "Requesting Party": {
                            "Insurance Company": "ABC Insurance",
                            "Handler": "John Doe",
                            "Carrier Claim Number": "12345"
                        },
                        "Insured Information": {
                            "Name": "Jane Smith",
                            "Contact #": "555-1234",
                            "Loss Address": "123 Elm Street",
                            "Public Adjuster": "Yes",
                            "Is the insured an Owner or a Tenant of the loss location?": "Owner"
                        },
                        "Adjuster Information": {
                            "Adjuster Name": "Mike Johnson",
                            "Adjuster Phone Number": "555-5678",
                            "Adjuster Email": "mike.johnson@example.com",
                            "Job Title": "Senior Adjuster",
                            "Address": "456 Oak Avenue",
                            "Policy #": "P987654321"
                        },
                        "Assignment Information": {
                            "Date of Loss/Occurrence": "01/15/2024",
                            "Cause of loss": "Wind",
                            "Facts of Loss": "Severe storm caused roof damage.",
                            "Loss Description": "Damaged shingles and gutters.",
                            "Residence Occupied During Loss": "Yes",
                            "Was Someone home at time of damage": "Yes",
                            "Repair or Mitigation Progress": "Repairs underway",
                            "Type": "Structural",
                            "Inspection type": "Initial",
                            "Wind": True,
                            "Structural": False,
                            "Hail": False,
                            "Foundation": False,
                            "Other - provide details": None,
                            "Additional details/Special Instructions": "Inspect foundation as well.",
                            "Attachments": ["photo1.jpg", "report.pdf"]
                        }
                    })
                }
            )
        ]
        mock_openai_create.return_value = mock_response

        email_body = "Sample email content with all required fields."

        extracted_data = self.parser.extract_with_llm(email_body)
        expected_data = {
            "Requesting Party": {
                "Insurance Company": "ABC Insurance",
                "Handler": "John Doe",
                "Carrier Claim Number": "12345"
            },
            "Insured Information": {
                "Name": "Jane Smith",
                "Contact #": "555-1234",
                "Loss Address": "123 Elm Street",
                "Public Adjuster": "Yes",
                "Is the insured an Owner or a Tenant of the loss location?": "Owner"
            },
            "Adjuster Information": {
                "Adjuster Name": "Mike Johnson",
                "Adjuster Phone Number": "555-5678",
                "Adjuster Email": "mike.johnson@example.com",
                "Job Title": "Senior Adjuster",
                "Address": "456 Oak Avenue",
                "Policy #": "P987654321"
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "01/15/2024",
                "Cause of loss": "Wind",
                "Facts of Loss": "Severe storm caused roof damage.",
                "Loss Description": "Damaged shingles and gutters.",
                "Residence Occupied During Loss": "Yes",
                "Was Someone home at time of damage": "Yes",
                "Repair or Mitigation Progress": "Repairs underway",
                "Type": "Structural",
                "Inspection type": "Initial",
                "Wind": True,
                "Structural": False,
                "Hail": False,
                "Foundation": False,
                "Other - provide details": None,
                "Additional details/Special Instructions": "Inspect foundation as well.",
                "Attachments": ["photo1.jpg", "report.pdf"]
            }
        }

        self.assertEqual(extracted_data, expected_data)
    
    def test_validate_data_success(self):
        # Sample valid data
        data = {
            "Requesting Party": {
                "Insurance Company": "ABC Insurance",
                "Handler": "John Doe",
                "Carrier Claim Number": "12345"
            },
            "Insured Information": {
                "Name": "Jane Smith",
                "Contact #": "555-1234",
                "Loss Address": "123 Elm Street"
            },
            "Adjuster Information": {
                "Adjuster Name": "Mike Johnson",
                "Adjuster Phone Number": "555-5678",
                "Adjuster Email": "mike.johnson@example.com"
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "01/15/2024",
                "Cause of loss": "Wind",
                "Loss Description": "Damaged shingles and gutters."
            }
        }

        is_valid = self.parser.validate_data(data)
        self.assertTrue(is_valid)
    
    def test_validate_data_failure_missing_field(self):
        # Data missing a required field
        data = {
            "Requesting Party": {
                "Insurance Company": "ABC Insurance",
                "Handler": "John Doe",
                # "Carrier Claim Number" is missing
            },
            "Insured Information": {
                "Name": "Jane Smith",
                "Contact #": "555-1234",
                "Loss Address": "123 Elm Street"
            },
            "Adjuster Information": {
                "Adjuster Name": "Mike Johnson",
                "Adjuster Phone Number": "555-5678",
                "Adjuster Email": "mike.johnson@example.com"
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "01/15/2024",
                "Cause of loss": "Wind",
                "Loss Description": "Damaged shingles and gutters."
            }
        }

        is_valid = self.parser.validate_data(data)
        self.assertFalse(is_valid)
    
    def test_score_confidence_high(self):
        # Data with minimal missing optional fields
        data = {
            "Requesting Party": {
                "Insurance Company": "ABC Insurance",
                "Handler": "John Doe",
                "Carrier Claim Number": "12345"
            },
            "Insured Information": {
                "Name": "Jane Smith",
                "Contact #": "555-1234",
                "Loss Address": "123 Elm Street",
                "Public Adjuster": "Yes",
                "Is the insured an Owner or a Tenant of the loss location?": "Owner"
            },
            "Adjuster Information": {
                "Adjuster Name": "Mike Johnson",
                "Adjuster Phone Number": "555-5678",
                "Adjuster Email": "mike.johnson@example.com",
                "Job Title": "Senior Adjuster",
                "Address": "456 Oak Avenue",
                "Policy #": "P987654321"
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "01/15/2024",
                "Cause of loss": "Wind",
                "Loss Description": "Damaged shingles and gutters.",
                "Wind": True,
                "Structural": False,
                "Hail": False,
                "Foundation": False,
                "Other - provide details": None,
                "Additional details/Special Instructions": "Inspect foundation as well."
            }
        }

        confidence = self.parser.score_confidence(data, "Sample email body.")
        self.assertGreaterEqual(confidence, 0.90)
    
    def test_score_confidence_low(self):
        # Data with multiple missing optional fields
        data = {
            "Requesting Party": {
                "Insurance Company": "ABC Insurance",
                "Handler": "John Doe",
                "Carrier Claim Number": "12345"
            },
            "Insured Information": {
                "Name": "Jane Smith",
                "Contact #": "555-1234",
                "Loss Address": "123 Elm Street",
                "Public Adjuster": "",
                "Is the insured an Owner or a Tenant of the loss location?": ""
            },
            "Adjuster Information": {
                "Adjuster Name": "Mike Johnson",
                "Adjuster Phone Number": "555-5678",
                "Adjuster Email": "mike.johnson@example.com",
                "Job Title": "",
                "Address": "",
                "Policy #": ""
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "01/15/2024",
                "Cause of loss": "Wind",
                "Loss Description": "Damaged shingles and gutters.",
                "Wind": False,
                "Structural": False,
                "Hail": False,
                "Foundation": False,
                "Other - provide details": "",
                "Additional details/Special Instructions": ""
            }
        }

        confidence = self.parser.score_confidence(data, "Sample email body with missing fields.")
        self.assertLess(confidence, 0.85)

    @patch('src.email_parsing.openai.ChatCompletion.create')
    def test_parse_email_success(self, mock_openai_create):
        # Mock LLM response
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message={
                    'content': json.dumps({
                        "Requesting Party": {
                            "Insurance Company": "ABC Insurance",
                            "Handler": "John Doe",
                            "Carrier Claim Number": "12345"
                        },
                        "Insured Information": {
                            "Name": "Jane Smith",
                            "Contact #": "555-1234",
                            "Loss Address": "123 Elm Street",
                            "Public Adjuster": "Yes",
                            "Is the insured an Owner or a Tenant of the loss location?": "Owner"
                        },
                        "Adjuster Information": {
                            "Adjuster Name": "Mike Johnson",
                            "Adjuster Phone Number": "555-5678",
                            "Adjuster Email": "mike.johnson@example.com",
                            "Job Title": "Senior Adjuster",
                            "Address": "456 Oak Avenue",
                            "Policy #": "P987654321"
                        },
                        "Assignment Information": {
                            "Date of Loss/Occurrence": "01/15/2024",
                            "Cause of loss": "Wind",
                            "Facts of Loss": "Severe storm caused roof damage.",
                            "Loss Description": "Damaged shingles and gutters.",
                            "Residence Occupied During Loss": "Yes",
                            "Was Someone home at time of damage": "Yes",
                            "Repair or Mitigation Progress": "Repairs underway",
                            "Type": "Structural",
                            "Inspection type": "Initial",
                            "Wind": True,
                            "Structural": False,
                            "Hail": False,
                            "Foundation": False,
                            "Other - provide details": None,
                            "Additional details/Special Instructions": "Inspect foundation as well.",
                            "Attachments": ["photo1.jpg", "report.pdf"]
                        }
                    })
                }
            )
        ]
        mock_openai_create.return_value = mock_response

        # Mock email content
        raw_email = b"""From: assigner@example.com
To: assignments@keystoneexperts.com
Subject: Assignment Intake - Claim #12345

Insurance Company: ABC Insurance
Handler: John Doe
Carrier Claim Number: 12345

Name: Jane Smith
Contact #: 555-1234
Loss Address: 123 Elm Street
Public Adjuster: Yes
Is the insured an Owner or a Tenant of the loss location? Owner

Adjuster Name: Mike Johnson
Adjuster Phone Number: 555-5678
Adjuster Email: mike.johnson@example.com
Job Title: Senior Adjuster
Address: 456 Oak Avenue
Policy #: P987654321

Date of Loss/Occurrence: 01/15/2024
Cause of loss: Wind
Facts of Loss: Severe storm caused roof damage.
Loss Description: Damaged shingles and gutters.
Residence Occupied During Loss: Yes
Was Someone home at time of damage: Yes
Repair or Mitigation Progress: Repairs underway
Type: Structural
Inspection type: Initial

Wind [X]
Structural [ ]
Hail [ ]
Foundation [ ]
Other [] - provide details:

Additional details/Special Instructions: Inspect foundation as well.

Attachments: photo1.jpg, report.pdf
"""

        parsed_data = self.parser.parse_email(raw_email)
        expected_output = {
            "extracted_data": {
                "Requesting Party": {
                    "Insurance Company": "ABC Insurance",
                    "Handler": "John Doe",
                    "Carrier Claim Number": "12345"
                },
                "Insured Information": {
                    "Name": "Jane Smith",
                    "Contact #": "555-1234",
                    "Loss Address": "123 Elm Street",
                    "Public Adjuster": "Yes",
                    "Is the insured an Owner or a Tenant of the loss location?": "Owner"
                },
                "Adjuster Information": {
                    "Adjuster Name": "Mike Johnson",
                    "Adjuster Phone Number": "555-5678",
                    "Adjuster Email": "mike.johnson@example.com",
                    "Job Title": "Senior Adjuster",
                    "Address": "456 Oak Avenue",
                    "Policy #": "P987654321"
                },
                "Assignment Information": {
                    "Date of Loss/Occurrence": "01/15/2024",
                    "Cause of loss": "Wind",
                    "Facts of Loss": "Severe storm caused roof damage.",
                    "Loss Description": "Damaged shingles and gutters.",
                    "Residence Occupied During Loss": "Yes",
                    "Was Someone home at time of damage": "Yes",
                    "Repair or Mitigation Progress": "Repairs underway",
                    "Type": "Structural",
                    "Inspection type": "Initial",
                    "Wind": True,
                    "Structural": False,
                    "Hail": False,
                    "Foundation": False,
                    "Other - provide details": None,
                    "Additional details/Special Instructions": "Inspect foundation as well.",
                    "Attachments": ["photo1.jpg", "report.pdf"]
                }
            },
            "validation": {
                "is_valid": True
            },
            "confidence_score": 0.90,
            "needs_human_review": False
        }

        self.assertEqual(parsed_data, expected_output)
    
    def test_parse_email_missing_required_field(self):
        # Sample email missing a required field
        raw_email = b"""From: assigner@example.com
To: assignments@keystoneexperts.com
Subject: Assignment Intake - Claim #12345

Insurance Company: ABC Insurance
Handler: John Doe
# Carrier Claim Number is missing

Name: Jane Smith
Contact #: 555-1234
Loss Address: 123 Elm Street

Adjuster Name: Mike Johnson
Adjuster Phone Number: 555-5678
Adjuster Email: mike.johnson@example.com
Job Title: Senior Adjuster
Address: 456 Oak Avenue
Policy #: P987654321

Date of Loss/Occurrence: 01/15/2024
Cause of loss: Wind
Loss Description: Damaged shingles and gutters.

Wind [X]
Structural [ ]
Hail [ ]
Foundation [ ]
Other [] - provide details:

Additional details/Special Instructions: Inspect foundation as well.

Attachments: photo1.jpg, report.pdf
"""

        with patch('src.email_parsing.openai.ChatCompletion.create') as mock_openai_create:
            # Mock LLM response with missing Carrier Claim Number
            mock_response = MagicMock()
            mock_response.choices = [
                MagicMock(
                    message={
                        'content': json.dumps({
                            "Requesting Party": {
                                "Insurance Company": "ABC Insurance",
                                "Handler": "John Doe",
                                "Carrier Claim Number": None
                            },
                            "Insured Information": {
                                "Name": "Jane Smith",
                                "Contact #": "555-1234",
                                "Loss Address": "123 Elm Street",
                                "Public Adjuster": None,
                                "Is the insured an Owner or a Tenant of the loss location?": None
                            },
                            "Adjuster Information": {
                                "Adjuster Name": "Mike Johnson",
                                "Adjuster Phone Number": "555-5678",
                                "Adjuster Email": "mike.johnson@example.com",
                                "Job Title": "Senior Adjuster",
                                "Address": "456 Oak Avenue",
                                "Policy #": "P987654321"
                            },
                            "Assignment Information": {
                                "Date of Loss/Occurrence": "01/15/2024",
                                "Cause of loss": "Wind",
                                "Facts of Loss": None,
                                "Loss Description": "Damaged shingles and gutters.",
                                "Residence Occupied During Loss": None,
                                "Was Someone home at time of damage": None,
                                "Repair or Mitigation Progress": None,
                                "Type": None,
                                "Inspection type": None,
                                "Wind": True,
                                "Structural": False,
                                "Hail": False,
                                "Foundation": False,
                                "Other - provide details": None,
                                "Additional details/Special Instructions": "Inspect foundation as well.",
                                "Attachments": ["photo1.jpg", "report.pdf"]
                            }
                        })
                    }
                )
            ]
            mock_openai_create.return_value = mock_response

            parsed_data = self.parser.parse_email(raw_email)
            self.assertFalse(parsed_data["validation"]["is_valid"])
            self.assertTrue(parsed_data["needs_human_review"])
            self.assertLess(parsed_data["confidence
