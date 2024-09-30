import os
import pickle
import logging
import time
import random
from pathlib import Path
from typing import List

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Load environment variables from .env file
load_dotenv()

# Retrieve paths from environment variables
CREDENTIALS_PATH = Path(os.getenv('CREDENTIALS_PATH', 'credentials/credentials.json'))
TOKEN_PATH = Path(os.getenv('TOKEN_PATH', 'token.pickle'))
LOG_FILE = Path(os.getenv('LOG_FILE', 'email_retrieval.log'))

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format='%(asctime)s %(levelname)s:%(message)s'
)

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

class EmailRetrievalModule:
    def __init__(self, credentials_path: Path, token_path: Path):
        """
        Initializes the Email Retrieval Module with OAuth 2.0 credentials.

        :param credentials_path: Path to the OAuth 2.0 credentials JSON file.
        :param token_path: Path to the token pickle file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.service = self.authenticate()

    def authenticate(self) -> object:
        """
        Authenticates the user and returns the Gmail API service instance.

        :return: Gmail API service instance.
        """
        creds = None
        # Load existing credentials from token.pickle
        if self.token_path.exists():
            with open(self.token_path, 'rb') as token:
                creds = pickle.load(token)
                logging.info("Loaded credentials from token.pickle.")

        # If there are no valid credentials, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                    logging.info("Credentials refreshed.")
                except Exception as e:
                    logging.error(f"Error refreshing credentials: {e}")
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, SCOPES)
                    creds = flow.run_local_server(port=0)
                    logging.info("Obtained new credentials via OAuth flow.")
                except Exception as e:
                    logging.error(f"Error during OAuth flow: {e}")
                    raise e

            # Save the credentials for the next run
            with open(self.token_path, 'wb') as token:
                pickle.dump(creds, token)
                logging.info(f"Saved new credentials to {self.token_path}.")

        try:
            service = build('gmail', 'v1', credentials=creds)
            logging.info("Gmail service built successfully.")
            return service
        except Exception as e:
            logging.error(f"Failed to build Gmail service: {e}")
            raise e

    def get_unread_emails(self, max_results: int = 100) -> List[dict]:
        """
        Retrieves unread emails from the Gmail inbox.

        :param max_results: Maximum number of emails to retrieve.
        :return: List of email message objects.
        """
        try:
            response = self.service.users().messages().list(
                userId='me',
                labelIds=['UNREAD'],
                maxResults=max_results
            ).execute()

            messages = response.get('messages', [])
            logging.info(f"Retrieved {len(messages)} unread emails.")

            # Fetch full email data
            emails = []
            for msg in messages:
                try:
                    email = self.service.users().messages().get(
                        userId='me',
                        id=msg['id'],
                        format='full'
                    ).execute()
                    emails.append(email)
                    logging.info(f"Fetched email with ID: {msg['id']}")
                except HttpError as error:
                    logging.error(f"An error occurred while fetching email ID {msg['id']}: {error}")
                    self.handle_http_error(error)
            return emails

        except HttpError as error:
            logging.error(f"An error occurred during email retrieval: {error}")
            self.handle_http_error(error)
            return []

    def mark_as_read(self, email_id: str):
        """
        Marks the specified email as read.

        :param email_id: The ID of the email to mark as read.
        """
        try:
            self.service.users().messages().modify(
                userId='me',
                id=email_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()
            logging.info(f"Marked email ID {email_id} as read.")
        except HttpError as error:
            logging.error(f"Failed to mark email ID {email_id} as read: {error}")
            self.handle_http_error(error)

    def handle_http_error(self, error: HttpError, retries: int = 5):
        """
        Handles HTTP errors with exponential backoff.

        :param error: The HttpError encountered.
        :param retries: Number of retries before giving up.
        """
        if error.resp.status in [429, 500, 503]:
            for n in range(retries):
                sleep_time = (2 ** n) + (random.randint(0, 1000) / 1000)
                logging.warning(f"Rate limit hit or server error. Sleeping for {sleep_time} seconds.")
                time.sleep(sleep_time)
                try:
                    # Since we cannot retry the exact request, inform that a retry should be attempted externally
                    logging.info("Please retry the request externally.")
                    break
                except HttpError as e:
                    logging.error(f"Retry {n+1} failed: {e}")
            logging.error("Max retries exceeded.")
        else:
            logging.error(f"Non-retriable error occurred: {error}")
            raise error

if __name__ == "__main__":
    # Example usage
    email_module = EmailRetrievalModule(credentials_path=CREDENTIALS_PATH, token_path=TOKEN_PATH)
    unread_emails = email_module.get_unread_emails()

    for email in unread_emails:
        # Process each email as needed
        print(f"Email ID: {email['id']}")
        # After processing, mark as read
        email_module.mark_as_read(email['id'])
