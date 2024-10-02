# src/email_retrieval.py

"""
Email Retrieval Module

This module handles the retrieval of unread emails from a Gmail account using the Gmail API.
It manages authentication, fetches unread emails, and marks them as read after processing.
"""

import os
import pickle
import logging
import asyncio
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from filelock import FileLock, Timeout
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type

# Load environment variables from .env file
load_dotenv()

# Retrieve paths from environment variables
CREDENTIALS_PATH = Path(os.getenv("CREDENTIALS_PATH", "credentials/credentials.json"))
TOKEN_PATH = Path(os.getenv("TOKEN_PATH", "token.pickle"))
LOG_FILE = Path(os.getenv("LOG_FILE", "logs/email_retrieval.log"))

# Ensure log directory exists
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s %(levelname)s:%(message)s",
)

# If modifying these SCOPES, delete the file token.pickle.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


class EmailRetrievalError(Exception):
    """Custom exception for email retrieval errors."""
    pass


class EmailRetrievalModule:
    """Handles authentication and retrieval of unread emails from Gmail."""

    def __init__(self, credentials_path: Path, token_path: Path):
        """
        Initializes the Email Retrieval Module with OAuth 2.0 credentials.

        :param credentials_path: Path to the OAuth 2.0 credentials JSON file.
        :param token_path: Path to the token pickle file.
        """
        self.credentials_path = credentials_path
        self.token_path = token_path
        self.lock = FileLock(f"{self.token_path}.lock")
        self.service = self.authenticate()

    def authenticate(self) -> Optional[object]:
        """
        Authenticates the user and returns the Gmail API service instance.

        :return: Gmail API service instance or None if authentication fails.
        :raises EmailRetrievalError: If authentication fails.
        """
        creds = None
        try:
            with self.lock.acquire(timeout=10):
                # Load existing credentials from token.pickle
                if self.token_path.exists():
                    with open(self.token_path, "rb") as token_file:
                        creds = pickle.load(token_file)
                        logging.info("Loaded credentials from token.pickle.")

                # If there are no valid credentials, let the user log in.
                if not creds or not creds.valid:
                    if creds and creds.expired and creds.refresh_token:
                        try:
                            creds.refresh(Request())
                            logging.info("Credentials refreshed.")
                        except Exception as exc:
                            logging.error("Error refreshing credentials: %s", exc)
                            raise EmailRetrievalError(
                                "Failed to refresh credentials."
                            ) from exc
                    else:
                        creds = self.obtain_new_credentials()

                    # Save the credentials for the next run
                    with open(self.token_path, "wb") as token_file:
                        pickle.dump(creds, token_file)
                        logging.info("Saved new credentials to token.pickle.")

            service = build("gmail", "v1", credentials=creds)
            logging.info("Gmail service built successfully.")
            return service

        except Timeout as exc:
            logging.error("Could not acquire lock on the token file.")
            raise EmailRetrievalError(
                "Failed to acquire lock on the token file."
            ) from exc
        except Exception as exc:
            logging.error("Authentication failed: %s", exc)
            raise EmailRetrievalError(f"Authentication failed: {str(exc)}") from exc

    def obtain_new_credentials(self) -> Credentials:
        """
        Obtains new OAuth 2.0 credentials via the Installed App Flow.

        :return: New credentials object.
        :raises EmailRetrievalError: If obtaining new credentials fails.
        """
        try:
            flow = InstalledAppFlow.from_client_secrets_file(
                self.credentials_path, SCOPES
            )
            creds = flow.run_local_server(port=0)
            logging.info("Obtained new credentials via OAuth flow.")
            return creds
        except Exception as exc:
            logging.error("Error during OAuth flow: %s", exc)
            raise EmailRetrievalError(f"Error during OAuth flow: {str(exc)}") from exc

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(HttpError),
        reraise=True,
    )
    def get_unread_emails_sync(self, max_results: int = 100) -> List[dict]:
        """
        Synchronously retrieves unread emails from the Gmail inbox.

        :param max_results: Maximum number of emails to retrieve.
        :return: List of email message objects.
        :raises EmailRetrievalError: If email retrieval fails.
        """
        try:
            response = (
                self.service.users()
                .messages()
                .list(userId="me", labelIds=["UNREAD"], maxResults=max_results)
                .execute()
            )

            messages = response.get("messages", [])
            logging.info("Retrieved %d unread emails.", len(messages))

            # Fetch full email data
            emails = []
            for msg in messages:
                msg_id = msg.get("id")
                try:
                    email = (
                        self.service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="full")
                        .execute()
                    )
                    emails.append(email)
                    logging.debug("Fetched email with ID: %s", msg_id)
                except HttpError as error:
                    logging.error(
                        "An error occurred while fetching email ID %s: %s",
                        msg_id,
                        error,
                    )
                    self.handle_http_error(error)
            return emails

        except HttpError as error:
            logging.error("An error occurred during email retrieval: %s", error)
            self.handle_http_error(error)
            return []

    async def get_unread_emails(self, max_results: int = 100) -> List[dict]:
        """
        Asynchronously retrieves unread emails from the Gmail inbox.

        :param max_results: Maximum number of emails to retrieve.
        :return: List of email message objects.
        :raises EmailRetrievalError: If email retrieval fails.
        """
        loop = asyncio.get_event_loop()
        try:
            emails = await loop.run_in_executor(
                None, self.get_unread_emails_sync, max_results
            )
            return emails
        except Exception as exc:
            logging.error("Failed to asynchronously retrieve unread emails: %s", exc)
            raise EmailRetrievalError(f"Error retrieving emails: {str(exc)}") from exc

    def mark_as_read_sync(self, email_id: str):
        """
        Synchronously marks the specified email as read.

        :param email_id: The ID of the email to mark as read.
        :raises EmailRetrievalError: If marking as read fails.
        """
        try:
            self.service.users().messages().modify(
                userId="me", id=email_id, body={"removeLabelIds": ["UNREAD"]}
            ).execute()
            logging.info("Marked email ID %s as read.", email_id)
        except HttpError as error:
            logging.error("Failed to mark email ID %s as read: %s", email_id, error)
            self.handle_http_error(error)

    @retry(
        wait=wait_exponential(multiplier=1, min=4, max=60),
        stop=stop_after_attempt(5),
        retry=retry_if_exception_type(HttpError),
        reraise=True,
    )
    def handle_http_error(
        self,
        error: HttpError,
    ):
        """
        Handles HTTP errors with exponential backoff and retries the failed request if possible.

        :param error: The HttpError encountered.
        :raises HttpError: If all retries fail or if the error is non-retriable.
        """
        if error.resp.status in [429, 500, 503]:
            logging.warning(
                "Rate limit hit or server error (status %d). Initiating retry mechanism.",
                error.resp.status,
            )
            raise error  # Trigger tenacity retry
        else:
            logging.error("Non-retriable error occurred: %s", error)
            raise error

    async def mark_as_read(self, email_id: str):
        """
        Asynchronously marks the specified email as read.

        :param email_id: The ID of the email to mark as read.
        :raises EmailRetrievalError: If marking as read fails.
        """
        loop = asyncio.get_event_loop()
        try:
            await loop.run_in_executor(None, self.mark_as_read_sync, email_id)
        except Exception as exc:
            logging.error("Failed to asynchronously mark email ID %s as read: %s", email_id, exc)
            raise EmailRetrievalError(f"Error marking email as read: {str(exc)}") from exc


async def process_email(email_module: EmailRetrievalModule, email: dict):
    """
    Asynchronously processes a single email and marks it as read.

    :param email_module: Instance of EmailRetrievalModule.
    :param email: The email message object to process.
    """
    email_id = email.get("id")
    try:
        # Placeholder for email processing logic
        logging.info("Processing email ID: %s", email_id)
        # Simulate processing delay
        await asyncio.sleep(1)
        # After processing, mark as read
        await asyncio.wait_for(email_module.mark_as_read(email_id), timeout=30)
        logging.info("Successfully processed and marked email ID %s as read.", email_id)
    except asyncio.TimeoutError:
        logging.error("Timeout occurred while processing email ID: %s", email_id)
    except EmailRetrievalError as exc:
        logging.error("Failed to process email ID %s: %s", email_id, exc)


async def main():
    """
    Main asynchronous function to retrieve and process unread emails concurrently.
    """
    email_module = EmailRetrievalModule(
        credentials_path=CREDENTIALS_PATH, token_path=TOKEN_PATH
    )
    try:
        unread_emails = await email_module.get_unread_emails()

        if not unread_emails:
            logging.info("No unread emails to process.")
            return

        # Process emails concurrently
        results = await asyncio.gather(
            *(process_email(email_module, email) for email in unread_emails),
            return_exceptions=True
        )

        for result in results:
            if isinstance(result, Exception):
                logging.error(f"Error in processing email: {result}")

    except EmailRetrievalError as exc:
        logging.error("Email retrieval process failed: %s", exc)


if __name__ == "__main__":
    # Run the main asynchronous function
    asyncio.run(main())
