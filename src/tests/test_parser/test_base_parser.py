# tests/test_parser/test_base_parser.py

"""
Unit tests for the BaseParser class and its implementations.
"""

import pytest
from src.parsers.base_parser import BaseParser


def test_base_parser_instantiation():
    """
    Test that a subclass of BaseParser can be instantiated.
    """
    class ConcreteParser(BaseParser):
        """
        A concrete implementation of BaseParser for testing purposes.
        """
        def parse(self, email_content: str):
            return {}

    parser = ConcreteParser()
    assert isinstance(parser, BaseParser)


def test_base_parser_parse_not_implemented():
    """
    Test that a subclass without parse implementation raises a NotImplementedError.
    """
    class IncompleteParser(BaseParser):
        """
        A subclass of BaseParser without a concrete parse implementation.
        """
        def parse(self, email_content: str):
            raise NotImplementedError("This parser method is not implemented.")

    parser = IncompleteParser()

    with pytest.raises(NotImplementedError):
        parser.parse("Test email content")


def test_preprocess_email():
    """
    Test the email preprocessing step to ensure it removes unwanted sections.
    """
    class ConcreteParser(BaseParser):
        """
        A concrete implementation of BaseParser used to test preprocessing.
        """
        def parse(self, email_content: str):
            return {}

    parser = ConcreteParser()
    raw_email = """Hello Team,

    Please find the details below.

    Regards,
    John Doe
    -- 
    Company Confidential
    """
    expected_processed = """Hello Team,

    Please find the details below."""
    assert parser.preprocess_email(raw_email) == expected_processed
