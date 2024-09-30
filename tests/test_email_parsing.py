# tests/test_email_parsing.py

import pytest
from unittest.mock import patch, MagicMock

from src.email_parsing import EmailParser, EmailParsingError


@pytest.fixture
def sample_email_content():
    return """
    Subject: Claim Number 12345 - Forensic Engineering Services Required

    Dear Team,

    We require your services for the following claim:

    Requesting Party Insurance Company: ABC Insurance
    Handler: John Doe
    Carrier Claim Number: 12345
    Insured Information:
        Name: Jane Smith
        Contact #: (555) 123-4567
        Loss Address: 123 Elm Street, Springfield
        Public Adjuster: XYZ Adjusters
        Owner

    Adjuster Information:
        Adjuster Name: Mike Johnson
        Adjuster Phone Number: (555) 987-6543
        Adjuster Email: mike.johnson@abcinsurance.com
        Job Title: Senior Adjuster
        Address: 456 Oak Avenue, Springfield
        Policy #: P-67890

    Assignment Information:
        Date of Loss/Occurrence: 09/15/2023
        Cause of loss: Hail
        Facts of Loss: Severe hailstorm caused extensive damage to the roof and exterior.
        Loss Description: Multiple shingles damaged, windows broken.
        Residence Occupied During Loss: Yes
        Someone home at time of damage: No
        Repair or Mitigation Progress: Tarp applied to roof
        Type: Inspection
        Inspection type: Structural

    Check the box of applicable assignment type:
        Wind [ ]
        Structural [x]
        Hail [x]
        Foundation [ ]
        Other []

    Additional details/Special Instructions:
        Please prioritize this assignment as it is marked high priority.

    Attachment(s):
    """

@pytest.fixture
def mocked_parser_factory():
    with patch('src.email_parsing.ParserFactory') as MockFactory:
        factory_instance = MockFactory.return_value
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            "Requesting Party Insurance Company": "ABC Insurance",
            "Carrier Claim Number": "12345",
            "Insured Information": {
                "Name": "Jane Smith",
                "Contact #": "(555) 123-4567",
                "Loss Address": "123 Elm Street, Springfield",
                "Public Adjuster": "XYZ Adjusters",
                "Ownership": "Owner"
            },
            "Adjuster Information": {
                "Adjuster Name": "Mike Johnson",
                "Adjuster Phone Number": "(555) 987-6543",
                "Adjuster Email": "mike.johnson@abcinsurance.com",
                "Job Title": "Senior Adjuster",
                "Address": "456 Oak Avenue, Springfield",
                "Policy #": "P-67890"
            },
            "Assignment Information": {
                "Date of Loss/Occurrence": "09/15/2023",
                "Cause of loss": "Hail",
                "Facts of Loss": "Severe hailstorm caused extensive damage to the roof and exterior.",
                "Loss Description": "Multiple shingles damaged, windows broken.",
                "Residence Occupied During Loss": "Yes",
                "Someone home at time of damage": "No",
                "Repair or Mitigation Progress": "Tarp applied to roof",
                "Type": "Inspection",
                "Inspection type": "Structural"
            },
            "Assignment Type": {
                "Wind": False,
                "Structural": True,
                "Hail": True,
                "Foundation": False,
                "Other": False
            },
            "Additional details/Special Instructions": "Please prioritize this assignment as it is marked high priority.",
            "Attachments": []
        }
        factory_instance.get_parser.return_value = mock_parser
        yield MockFactory

@pytest.fixture
def mocked_openai():
    with patch('src.email_parsing.openai.ChatCompletion.create') as mock_openai:
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message={
                    'content': '{"Requesting Party Insurance Company": "ABC Insurance", "Carrier Claim Number": "12345", "Insured Information": {"Name": "Jane Smith", "Contact #": "(555) 123-4567", "Loss Address": "123 Elm Street, Springfield", "Public Adjuster": "XYZ Adjusters", "Ownership": "Owner"}, "Adjuster Information": {"Adjuster Name": "Mike Johnson", "Adjuster Phone Number": "(555) 987-6543", "Adjuster Email": "mike.johnson@abcinsurance.com", "Job Title": "Senior Adjuster", "Address": "456 Oak Avenue, Springfield", "Policy #": "P-67890"}, "Assignment Information": {"Date of Loss/Occurrence": "09/15/2023", "Cause of loss": "Hail", "Facts of Loss": "Severe hailstorm caused extensive damage to the roof and exterior.", "Loss Description": "Multiple shingles damaged, windows broken.", "Residence Occupied During Loss": "Yes", "Someone home at time of damage": "No", "Repair or Mitigation Progress": "Tarp applied to roof", "Type": "Inspection", "Inspection type": "Structural"}, "Assignment Type": {"Wind": false, "Structural": true, "Hail": true, "Foundation": false, "Other": false}, "Additional details/Special Instructions": "Please prioritize this assignment as it is marked high priority.", "Attachments": []}'
                }
            )
        ]
        mock_openai.return_value = mock_response
        yield mock_openai

def test_parse_email_success(sample_email_content, mocked_parser_factory, mocked_openai):
    from src.email_parsing import EmailParser

    parser = EmailParser()
    result = parser.parse_email(sample_email_content)

    assert result["Requesting Party Insurance Company"] == "ABC Insurance"
    assert result["Carrier Claim Number"] == "12345"
    assert result["Insured Information"]["Name"] == "Jane Smith"
    assert result["requires_manual_verification"] is True

def test_parse_email_missing_field(sample_email_content, mocked_parser_factory, mocked_openai):
    from src.email_parsing import EmailParser

    # Modify the parser to return data missing a required field
    mocked_parser_factory.return_value.get_parser.return_value.parse.return_value.pop("Carrier Claim Number")

    parser = EmailParser()

    with pytest.raises(EmailParsingError) as exc_info:
        parser.parse_email(sample_email_content)

    assert "Automated validation failed." in str(exc_info.value)

def test_parse_email_ai_failure(sample_email_content, mocked_parser_factory, mocked_openai):
    from src.email_parsing import EmailParser

    # Modify the AI response to be invalid JSON
    mocked_openai.return_value.choices[0].message['content'] = "This is not a JSON response."

    parser = EmailParser()

    with pytest.raises(EmailParsingError) as exc_info:
        parser.parse_email(sample_email_content)

    assert "AI-assisted review failed." in str(exc_info.value)

def test_parse_email_ai_validation_failure(sample_email_content, mocked_parser_factory, mocked_openai):
    from src.email_parsing import EmailParser

    # Modify the AI response to return incomplete data
    mocked_openai.return_value.choices[0].message['content'] = '{"Requesting Party Insurance Company": "", "Carrier Claim Number": "12345"}'

    parser = EmailParser()

    # Assuming ai_validation simply returns True in the current implementation,
    # we need to modify it to simulate a validation failure.
    with patch.object(EmailParser, 'ai_validation', return_value=False):
        with pytest.raises(EmailParsingError) as exc_info:
            parser.parse_email(sample_email_content)

    assert "AI-assisted validation failed." in str(exc_info.value)
