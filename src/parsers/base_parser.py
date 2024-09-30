# src/parsers/base_parser.py

from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseParser(ABC):
    """
    Abstract base class for all email parsers.
    Defines the interface and common functionalities.
    """

    @abstractmethod
    def parse(self, email_content: str) -> Dict[str, Any]:
        """
        Parse the given email content and extract relevant data.

        :param email_content: The raw content of the email.
        :return: A dictionary containing the extracted data.
        """
        pass

    def preprocess_email(self, email_content: str) -> str:
        """
        Preprocess the email content before parsing.
        Can include steps like removing signatures, disclaimers, etc.

        :param email_content: The raw content of the email.
        :return: Preprocessed email content.
        """
        # Example preprocessing steps
        lines = email_content.splitlines()
        processed_lines = []
        for line in lines:
            # Skip common footer lines
            if line.startswith('--') or line.startswith('Regards,') or line.startswith('Best,'):
                continue
            processed_lines.append(line)
        return '\n'.join(processed_lines)
