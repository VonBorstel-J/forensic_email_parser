# src/utils/config.py

import os
import logging
from dotenv import load_dotenv

class Config:
    def __init__(self):
        load_dotenv()
        # LLM API Keys
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        self.ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
        self.GOOGLE_API_KEY = os.getenv('GOOGLE_API_KEY')
        
        # Log file configuration
        log_dir = os.getenv('LOG_DIR', '../logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        self.LOG_FILE = os.path.join(log_dir, 'email_parsing.log')
        
        # Other configurations
        self.DEFAULT_PARSER = os.getenv('DEFAULT_PARSER', 'llm')  # options: llm, local_llm, rule_based
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # options: openai, anthropic, google
        self.LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4')
        self.LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'EleutherAI/gpt-neo-2.7B')

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(filename=self.LOG_FILE,
                            level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info('Logging is set up.')

