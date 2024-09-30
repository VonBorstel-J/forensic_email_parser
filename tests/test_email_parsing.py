# test_email_parsing.py

import pytest
from unittest.mock import patch, MagicMock
from email_parsing import EmailParser, EmailParsingError


@pytest.fixture
def sample_email_content():
    return """
    Subject: Claim Number 12345 - Forensic Engineering Services Required

    Requesting Party Insurance Company: ABC Insurance
    Handler: John Doe
    Carrier Claim Number: 12345
    Insured Information:
        Name: Jane Smith
        Contact #: (555) 123-4567
        Loss Address: 123 Elm Street, Springfield
    """


@pytest.fixture
def malformed_email_content():
    return """
    Subject: Claim Number 12345

    No other required information here.
    """


@pytest.fixture
def mocked_parser_factory():
    with patch("src.email_parsing.ParserFactory") as MockFactory:
        factory_instance = MockFactory.return_value
        mock_parser = MagicMock()
        mock_parser.parse.return_value = {
            "Carrier Claim Number": "12345",
            "Insured Information": "Jane Smith",
            "Adjuster Information": "John Doe",
        }
        factory_instance.get_parser.return_value = mock_parser
        yield MockFactory


@pytest.fixture
def mocked_openai():
    with patch("src.email_parsing.openai.ChatCompletion.create") as mock_openai:
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message={"content": '{"Carrier Claim Number": "12345"}'})
        ]
        mock_openai.return_value = mock_response
        yield mock_openai


def test_email_parser_success(
    sample_email_content, mocked_parser_factory, mocked_openai
):
    parser = EmailParser()
    result = parser.parse_email(sample_email_content)
    assert result["Carrier Claim Number"] == "12345"


def test_email_parser_malformed(malformed_email_content, mocked_parser_factory):
    parser = EmailParser()
    with pytest.raises(EmailParsingError):
        parser.parse_email(malformed_email_content)


def test_email_parser_openai_error(sample_email_content, mocked_parser_factory):
    with patch(
        "src.email_parsing.openai.ChatCompletion.create",
        side_effect=Exception("OpenAI API failed"),
    ):
        parser = EmailParser()
        with pytest.raises(Exception):
            parser.parse_email(sample_email_content)
