# tests/test_parser/test_parser_factory.py

import pytest
from unittest.mock import patch, MagicMock
from src.parsers.parser_factory import ParserFactory
from src.parsers.rule_based_parser import RuleBasedParser
from src.parsers.llm_parser import LLMParser
from src.parsers.local_llm_parser import LocalLLMParser



@pytest.fixture
def well_structured_email():
    return """
    Requesting Party Insurance Company: ABC Insurance
    Handler: John Doe
    Carrier Claim Number: 12345
    Insured Information:
        Name: Jane Smith
        Contact #: (555) 123-4567
        Loss Address: 123 Elm Street, Springfield
        Public Adjuster: XYZ Adjusters

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

    Additional details/Special Instructions:
        Please prioritize this assignment as it is marked high priority.
    """

@pytest.fixture
def unstructured_email():
    return """
    Hi Team,

    We need to handle a new claim urgently. The details are as follows:

    ABC Insurance has filed a claim (No. 12345) for damages caused by a hailstorm on September 15, 2023. The insured, Jane Smith, resides at 123 Elm Street, Springfield. The adjuster assigned is Mike Johnson, reachable at (555) 987-6543 or mike.johnson@abcinsurance.com.

    Please prioritize this task and provide a report ASAP.

    Thanks,
    John Doe
    """

@pytest.fixture
def mocked_local_llm():
    with patch('src.parsers.parser_factory.LocalLLMParser') as mock_local_llm:
        instance = mock_local_llm.return_value
        instance.parse.return_value = {"dummy": "data"}
        yield mock_local_llm

@pytest.fixture
def mocked_llm():
    with patch('src.parsers.parser_factory.LLMParser') as mock_llm:
        instance = mock_llm.return_value
        instance.parse.return_value = {"dummy": "data"}
        yield mock_llm

def test_get_parser_rule_based(well_structured_email, mocked_local_llm, mocked_llm):
    with patch('src.parsers.parser_factory.Config') as mock_config:
        mock_config.USE_LOCAL_LLM = False
        parser_factory = ParserFactory()
        parser = parser_factory.get_parser(well_structured_email)
        assert isinstance(parser, RuleBasedParser)

def test_get_parser_llm(mocked_local_llm, mocked_llm):
    unstructured_email = """
    Hi Team,

    We need to handle a new claim urgently. The details are as follows:

    ABC Insurance has filed a claim (No. 12345) for damages caused by a hailstorm on September 15, 2023. The insured, Jane Smith, resides at 123 Elm Street, Springfield. The adjuster assigned is Mike Johnson, reachable at (555) 987-6543 or mike.johnson@abcinsurance.com.

    Please prioritize this task and provide a report ASAP.

    Thanks,
    John Doe
    """

    with patch('src.parsers.parser_factory.Config') as mock_config:
        mock_config.USE_LOCAL_LLM = False
        parser_factory = ParserFactory()
        parser = parser_factory.get_parser(unstructured_email)
        assert isinstance(parser, LLMParser)

def test_get_parser_local_llm(unstructured_email, mocked_local_llm, mocked_llm):
    with patch('src.parsers.parser_factory.Config') as mock_config:
        mock_config.USE_LOCAL_LLM = True
        parser_factory = ParserFactory()
        parser = parser_factory.get_parser(unstructured_email)
        assert isinstance(parser, LocalLLMParser)
