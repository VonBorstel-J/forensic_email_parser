#src\parsers\parser_factory.py

"""
This module contains the ParserFactory class that selects the appropriate parser.
"""

import logging
from utils.config import Config
from .rule_based_parser import RuleBasedParser
from .llm_parser import LLMParser
from .local_llm_parser import LocalLLMParser



class ParserFactory:
    """Factory class to instantiate the appropriate parser based on email content or user preferences."""

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self.use_local_llm = Config.USE_LOCAL_LLM
        self.logger.info(
            "ParserFactory initialized. Use Local LLM: %s", self.use_local_llm
        )

    def get_parser(
        self, email_content: str, email_id: str, user_preferences: dict = None
    ):
        """
        Determines which parser to use based on user preferences or email content characteristics.
        """
        try:
            self.logger.info("Selecting parser for email ID %s.", email_id)

            if user_preferences and "preferred_parser" in user_preferences:
                preferred_parser = user_preferences["preferred_parser"]
                if preferred_parser == "rule-based":
                    parser = RuleBasedParser()
                elif preferred_parser == "llm":
                    parser = LLMParser()
                elif preferred_parser == "local-llm":
                    parser = LocalLLMParser()
                else:
                    raise ValueError(f"Unknown preferred parser: {preferred_parser}")
                self.logger.info(
                    "Email ID %s: User preference selected parser %s",
                    email_id,
                    parser.__class__.__name__,
                )
                return parser

            preprocessed_content = self.preprocess_email(email_content).lower()
            if self.is_rule_based_applicable(preprocessed_content):
                parser = RuleBasedParser()
                self.logger.info(
                    "Email ID %s: RuleBasedParser selected based on content analysis.",
                    email_id,
                )
            else:
                parser = LocalLLMParser() if self.use_local_llm else LLMParser()
                self.logger.info(
                    "Email ID %s: %s selected based on content analysis.",
                    email_id,
                    parser.__class__.__name__,
                )
            return parser

        except ValueError as ve:
            self.logger.error("ValueError for email ID %s: %s", email_id, ve)
            raise
        except Exception as e:
            self.logger.exception(
                "Unexpected error occurred while selecting parser for email ID %s.",
                email_id,
            )
            raise

    def is_rule_based_applicable(self, content: str) -> bool:
        """
        Determine if the rule-based parser is suitable for the given email content.
        """
        try:
            rule_based_keywords = [
                "carrier claim number",
                "insured information",
                "adjuster information",
            ]
            for keyword in rule_based_keywords:
                if keyword not in content:
                    self.logger.debug(
                        "Keyword '%s' not found in email content.", keyword
                    )
                    return False
            self.logger.info(
                "All required keywords found. Rule-based parser applicable."
            )
            return True
        except Exception as e:
            self.logger.exception("Error during rule-based applicability check.")
            raise

    def preprocess_email(self, email_content: str) -> str:
        """
        Preprocess the email content before parser selection.
        """
        try:
            return email_content.strip()
        except Exception as e:
            self.logger.exception("Error during email preprocessing.")
            raise
