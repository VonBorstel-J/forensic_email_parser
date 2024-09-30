# tests/test_parser/test_local_llm_parser.py
from unittest.mock import patch, MagicMock
import pytest
import requests
from parsers.local_llm_parser import LocalLLMParser

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
def mocked_requests_post():
    with patch('src.parsers.local_llm_parser.requests.post') as mock_post:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "choices": [
                {
                    "message": {
                        "content": json.dumps({
                            "Requesting Party Insurance Company": "ABC Insurance",
                            "Handler": "John Doe",
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
                                "Policy Number": "P-67890"
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
                            "Attachments": ""
                        })
                    }
                }
            ]
        }
        mock_post.return_value = mock_response
        yield mock_post

def test_local_llm_parser_success(sample_email_content, mocked_requests_post):
    parser = LocalLLMParser()
    extracted_data = parser.parse(sample_email_content)

    assert extracted_data["Requesting Party Insurance Company"] == "ABC Insurance"
    assert extracted_data["Handler"] == "John Doe"
    assert extracted_data["Carrier Claim Number"] == "12345"
    assert extracted_data["Insured Information"]["Name"] == "Jane Smith"
    assert extracted_data["Insured Information"]["Contact #"] == "(555) 123-4567"
    assert extracted_data["Insured Information"]["Loss Address"] == "123 Elm Street, Springfield"
    assert extracted_data["Insured Information"]["Public Adjuster"] == "XYZ Adjusters"
    assert extracted_data["Insured Information"]["Ownership"] == "Owner"
    assert extracted_data["Adjuster Information"]["Adjuster Name"] == "Mike Johnson"
    assert extracted_data["Adjuster Information"]["Adjuster Phone Number"] == "(555) 987-6543"
    assert extracted_data["Adjuster Information"]["Adjuster Email"] == "mike.johnson@abcinsurance.com"
    assert extracted_data["Adjuster Information"]["Job Title"] == "Senior Adjuster"
    assert extracted_data["Adjuster Information"]["Address"] == "456 Oak Avenue, Springfield"
    assert extracted_data["Adjuster Information"]["Policy Number"] == "P-67890"
    assert extracted_data["Assignment Information"]["Date of Loss/Occurrence"] == "09/15/2023"
    assert extracted_data["Assignment Information"]["Cause of loss"] == "Hail"
    assert extracted_data["Assignment Information"]["Facts of Loss"] == "Severe hailstorm caused extensive damage to the roof and exterior."
    assert extracted_data["Assignment Information"]["Loss Description"] == "Multiple shingles damaged, windows broken."
    assert extracted_data["Assignment Information"]["Residence Occupied During Loss"] == "Yes"
    assert extracted_data["Assignment Information"]["Someone home at time of damage"] == "No"
    assert extracted_data["Assignment Information"]["Repair or Mitigation Progress"] == "Tarp applied to roof"
    assert extracted_data["Assignment Information"]["Type"] == "Inspection"
    assert extracted_data["Assignment Information"]["Inspection type"] == "Structural"
    assert extracted_data["Assignment Type"]["Wind"] is False
    assert extracted_data["Assignment Type"]["Structural"] is True
    assert extracted_data["Assignment Type"]["Hail"] is True
    assert extracted_data["Assignment Type"]["Foundation"] is False
    assert extracted_data["Assignment Type"]["Other"] is False
    assert extracted_data["Additional details/Special Instructions"] == "Please prioritize this assignment as it is marked high priority."
    assert extracted_data["Attachments"] == ""

def test_local_llm_parser_invalid_json(sample_email_content, mocked_requests_post):
    # Modify the mocked response to return invalid JSON
    mocked_requests_post.return_value.json.return_value["choices"][0]["message"]["content"] = "This is not a JSON response."

    parser = LocalLLMParser()

    with pytest.raises(json.JSONDecodeError):
        parser.parse(sample_email_content)

def test_local_llm_parser_api_error(sample_email_content):
    with patch('src.parsers.local_llm_parser.requests.post', side_effect=requests.exceptions.RequestException("Connection Error")):
        parser = LocalLLMParser()
        with pytest.raises(requests.exceptions.RequestException):
            parser.parse(sample_email_content)
