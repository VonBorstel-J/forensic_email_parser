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

        # Check if API keys are present
        if not self.OPENAI_API_KEY:
            logging.warning('OPENAI_API_KEY is not set in the environment.')
        if not self.ANTHROPIC_API_KEY:
            logging.warning('ANTHROPIC_API_KEY is not set in the environment.')
        if not self.GOOGLE_API_KEY:
            logging.warning('GOOGLE_API_KEY is not set in the environment.')

        # Log file configuration
        log_dir = os.getenv('LOG_DIR', '../logs')
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.LOG_FILE = os.path.join(log_dir, 'email_parsing.log')

        # Other configurations
        self.DEFAULT_PARSER = os.getenv('DEFAULT_PARSER', 'llm')
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')
        self.LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-4')
        self.LOCAL_LLM_MODEL = os.getenv('LOCAL_LLM_MODEL', 'EleutherAI/gpt-neo-2.7B')

        # Setup logging
        self.setup_logging()

    def setup_logging(self):
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

        file_handler = logging.FileHandler(self.LOG_FILE)
        file_handler.setLevel(logging.INFO)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        logging.getLogger().addHandler(file_handler)
        logging.getLogger().addHandler(console_handler)

        logging.info('Logging is set up.')
