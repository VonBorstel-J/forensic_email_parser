# tests/test_parser/test_base_parser.py

import pytest
from src.parsers.base_parser import BaseParser


def test_base_parser_instantiation():
    class ConcreteParser(BaseParser):
        def parse(self, email_content: str):
            return {}

    parser = ConcreteParser()
    assert isinstance(parser, BaseParser)


def test_base_parser_parse_not_implemented():
    class IncompleteParser(BaseParser):
        pass

    with pytest.raises(TypeError):
        IncompleteParser()


def test_preprocess_email():
    class ConcreteParser(BaseParser):
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
