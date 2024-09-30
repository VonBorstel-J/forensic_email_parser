# tests/test_parser/test_rule_based_parser.py

import pytest
from src.parsers.rule_based_parser import RuleBasedParser


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
def incomplete_email_content():
    return """
    Subject: Claim Number 12345 - Forensic Engineering Services Required

    Dear Team,

    We require your services for the following claim:

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

def test_rule_based_parser_success(sample_email_content):
    parser = RuleBasedParser()
    extracted_data = parser.parse(sample_email_content)

    assert extracted_data["Requesting Party Insurance Company"] == "ABC Insurance"
    assert extracted_data["Handler"] == "John Doe"
    assert extracted_data["Carrier Claim Number"] == "12345"
    assert extracted_data["Insured Name"] == "Jane Smith"
    assert extracted_data["Insured Contact #"] == "(555) 123-4567"
    assert extracted_data["Loss Address"] == "123 Elm Street, Springfield"
    assert extracted_data["Public Adjuster"] == "XYZ Adjusters"
    assert extracted_data["Ownership"] == "Owner"
    assert extracted_data["Adjuster Name"] == "Mike Johnson"
    assert extracted_data["Adjuster Phone Number"] == "(555) 987-6543"
    assert extracted_data["Adjuster Email"] == "mike.johnson@abcinsurance.com"
    assert extracted_data["Job Title"] == "Senior Adjuster"
    assert extracted_data["Adjuster Address"] == "456 Oak Avenue, Springfield"
    assert extracted_data["Policy Number"] == "P-67890"
    assert extracted_data["Date of Loss/Occurrence"] == "09/15/2023"
    assert extracted_data["Cause of loss"] == "Hail"
    assert extracted_data["Facts of Loss"] == "Severe hailstorm caused extensive damage to the roof and exterior."
    assert extracted_data["Loss Description"] == "Multiple shingles damaged, windows broken."
    assert extracted_data["Residence Occupied During Loss"] == "Yes"
    assert extracted_data["Someone home at time of damage"] == "No"
    assert extracted_data["Repair or Mitigation Progress"] == "Tarp applied to roof"
    assert extracted_data["Type"] == "Inspection"
    assert extracted_data["Inspection type"] == "Structural"
    assert extracted_data["Assignment Type - Wind"] is False
    assert extracted_data["Assignment Type - Structural"] is True
    assert extracted_data["Assignment Type - Hail"] is True
    assert extracted_data["Assignment Type - Foundation"] is False
    assert extracted_data["Assignment Type - Other"] is False
    assert extracted_data["Additional details/Special Instructions"] == "Please prioritize this assignment as it is marked high priority."
    assert extracted_data["Attachments"] == ""

def test_rule_based_parser_missing_field(incomplete_email_content):
    parser = RuleBasedParser()
    extracted_data = parser.parse(incomplete_email_content)

    # "Requesting Party Insurance Company" is missing
    assert "Requesting Party Insurance Company" not in extracted_data or extracted_data["Requesting Party Insurance Company"] == ""
    assert extracted_data["Handler"] == "John Doe"
    # Other fields should be extracted correctly
    assert extracted_data["Carrier Claim Number"] == "12345"
    # ... other assertions can follow
    assert extracted_data["Ownership"] == "Owner"
