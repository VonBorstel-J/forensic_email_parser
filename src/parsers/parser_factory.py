# src/parsers/parser_factory.py

import logging

from .rule_based_parser import RuleBasedParser
from .llm_parser import LLMParser
from .local_llm_parser import LocalLLMParser
from utils.config import Config


class ParserFactory:
    """
    Factory class to instantiate the appropriate parser based on email content characteristics.
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.use_local_llm = Config.USE_LOCAL_LLM  # Boolean flag to choose between OpenAI and local LLM

    def get_parser(self, email_content: str):
        """
        Determine which parser to use based on email content and instantiate it.

        :param email_content: The raw content of the email.
        :return: An instance of a parser that inherits from BaseParser.
        """
        # Simple heuristic: If email contains specific keywords, choose rule-based; else, use LLM
        preprocessed_content = self.preprocess_email(email_content).lower()

        if self.is_rule_based_applicable(preprocessed_content):
            self.logger.info("Using RuleBasedParser for parsing.")
            return RuleBasedParser()
        else:
            if self.use_local_llm:
                self.logger.info("Using LocalLLMParser for parsing.")
                return LocalLLMParser()
            else:
                self.logger.info("Using LLMParser (OpenAI) for parsing.")
                return LLMParser()

    def is_rule_based_applicable(self, content: str) -> bool:
        """
        Determine if the rule-based parser is suitable for the given email content.

        :param content: Preprocessed email content in lowercase.
        :return: Boolean indicating if rule-based parsing should be used.
        """
        # Define keywords or patterns that indicate a well-structured email
        rule_based_keywords = [
            "requesting party insurance company",
            "carrier claim number",
            "insured information",
            "adjuster information",
            "assignment information",
            "additional details/special instructions"
        ]

        for keyword in rule_based_keywords:
            if keyword in content:
                continue
            else:
                return False
        return True
