import unittest
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.email_retrieval import EmailRetrievalModule

class TestEmailRetrievalModule(unittest.TestCase):
    @patch('src.email_retrieval.build')
    def test_authenticate_success(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        credentials_path = Path('credentials/credentials.json')
        token_path = Path('credentials/token.pickle')

        module = EmailRetrievalModule(credentials_path=credentials_path, token_path=token_path)
        self.assertEqual(module.service, mock_service)

    @patch('src.email_retrieval.build')
    def test_get_unread_emails(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users().messages().list().execute.return_value = {
            'messages': [{'id': '123'}, {'id': '456'}]
        }

        mock_service.users().messages().get().execute.side_effect = [
            {'id': '123', 'snippet': 'Test email 1'},
            {'id': '456', 'snippet': 'Test email 2'}
        ]

        credentials_path = Path('credentials/credentials.json')
        token_path = Path('credentials/token.pickle')

        module = EmailRetrievalModule(credentials_path=credentials_path, token_path=token_path)
        emails = module.get_unread_emails(max_results=2)

        self.assertEqual(len(emails), 2)
        self.assertEqual(emails[0]['id'], '123')
        self.assertEqual(emails[1]['id'], '456')

    @patch('src.email_retrieval.build')
    def test_mark_as_read(self, mock_build):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        credentials_path = Path('credentials/credentials.json')
        token_path = Path('credentials/token.pickle')

        module = EmailRetrievalModule(credentials_path=credentials_path, token_path=token_path)
        email_id = '123'

        module.mark_as_read(email_id)
        mock_service.users().messages().modify.assert_called_with(
            userId='me',
            id=email_id,
            body={'removeLabelIds': ['UNREAD']}
        )
        mock_service.users().messages().modify().execute.assert_called_once()

if __name__ == '__main__':
    unittest.main()
