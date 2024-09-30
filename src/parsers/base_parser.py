# base_parser.py

from abc import ABC, abstractmethod
from typing import Dict, Any
import logging


class BaseParser(ABC):
    """Abstract base class for all email parsers."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    def parse(self, email_content: str) -> Dict[str, Any]:
        """Parse the given email content and extract relevant data."""
        pass

    def preprocess_email(self, email_content: str) -> str:
        """Preprocess the email content before parsing."""
        try:
            lines = email_content.splitlines()
            processed_lines = []
            for line in lines:
                # Skip common footer lines
                if line.strip().startswith(("--", "Regards,", "Best,")):
                    continue
                processed_lines.append(line)
            preprocessed_content = "\n".join(processed_lines)
            return preprocessed_content
        except Exception as e:
            self.logger.exception("Error during email preprocessing.")
            raise
