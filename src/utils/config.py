# src/utils/config.py

import os
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        # LLM API Keys
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        
        # Other configurations
        self.LOG_FILE = os.getenv('LOG_FILE', '../logs/email_parsing.log')
        
        # Default Parser Settings
        self.DEFAULT_PARSER = os.getenv('DEFAULT_PARSER', 'llm')  # options: llm, local_llm, rule_based
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # options: openai, anthropic, google
        self.LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4')
        self.LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'EleutherAI/gpt-neo-2.7B')
