"""
Gmail API client wrapper for email monitoring.
Handles OAuth2 authentication and email operations.
"""

import base64
import logging
import pickle
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)


class GmailClient:
    """
    Gmail API client with error handling and rate limiting.
    Supports OAuth2 authentication and common email operations.
    """

    # Gmail API scopes
    SCOPES = [
        'https://www.googleapis.com/auth/gmail.readonly',  # Read emails
        'https://www.googleapis.com/auth/gmail.send',  # Send emails
        'https://www.googleapis.com/auth/gmail.modify'  # Mark as read/unread
    ]

    def __init__(self, credentials_path: str, token_path: str = None):
        """
        Initialize Gmail client.

        Args:
            credentials_path: Path to OAuth2 credentials.json file
            token_path: Path to store/load token.pickle (optional)
        """
        self.credentials_path = credentials_path
        self.token_path = token_path or credentials_path.replace('credentials.json', 'token.pickle')
        self.service = None
        self.user_email = None

    def authenticate(self) -> bool:
        """
        Authenticate with Gmail API using OAuth2.

        Returns:
            bool: True if authentication successful

        Raises:
            Exception: If authentication fails
        """
        try:
            creds = None

            # Load existing token
            if os.path.exists(self.token_path):
                logger.info(f"Loading existing token from {self.token_path}")
                with open(self.token_path, 'rb') as token:
                    creds = pickle.load(token)

            # If no valid credentials, authenticate
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Refreshing expired credentials")
                    creds.refresh(Request())
                else:
                    if not os.path.exists(self.credentials_path):
                        raise FileNotFoundError(
                            f"Credentials file not found: {self.credentials_path}\n"
                            "Please download OAuth2 credentials from Google Cloud Console"
                        )

                    logger.info("Starting OAuth2 flow")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_path, self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)

                # Save credentials for next run
                logger.info(f"Saving credentials to {self.token_path}")
                with open(self.token_path, 'wb') as token:
                    pickle.dump(creds, token)

            # Build Gmail service
            self.service = build('gmail', 'v1', credentials=creds)

            # Get authenticated user's email
            profile = self.service.users().getProfile(userId='me').execute()
            self.user_email = profile.get('emailAddress')

            logger.info(f"Successfully authenticated as {self.user_email}")
            return True

        except FileNotFoundError as e:
            logger.error(f"Credentials file error: {e}")
            raise
        except HttpError as e:
            logger.error(f"Gmail API error during authentication: {e}")
            raise
        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            raise

    def fetch_new_emails(
        self,
        since: datetime = None,
        query: str = None,
        max_results: int = 100
    ) -> List[Dict]:
        """
        Fetch new emails from inbox.

        Args:
            since: Only fetch emails after this datetime
            query: Gmail search query (e.g., "from:example@example.com")
            max_results: Maximum number of emails to fetch

        Returns:
            List of email dictionaries with parsed content

        Example:
            emails = client.fetch_new_emails(
                since=datetime.now() - timedelta(hours=1),
                query="is:unread"
            )
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Build query
            queries = []
            if query:
                queries.append(query)
            if since:
                # Gmail uses date format: YYYY/MM/DD
                date_str = since.strftime('%Y/%m/%d')
                queries.append(f'after:{date_str}')

            search_query = ' '.join(queries) if queries else None

            logger.info(f"Fetching emails with query: {search_query or 'all'}")

            # List messages
            results = self.service.users().messages().list(
                userId='me',
                q=search_query,
                maxResults=max_results
            ).execute()

            messages = results.get('messages', [])
            logger.info(f"Found {len(messages)} messages")

            # Fetch full message details
            emails = []
            for msg in messages:
                try:
                    email_data = self._fetch_email_detail(msg['id'])
                    if email_data:
                        emails.append(email_data)
                except Exception as e:
                    logger.error(f"Error fetching message {msg['id']}: {e}")
                    continue

            logger.info(f"Successfully fetched {len(emails)} emails")
            return emails

        except HttpError as e:
            logger.error(f"Gmail API error fetching emails: {e}")
            raise
        except Exception as e:
            logger.error(f"Error fetching emails: {e}")
            raise

    def _fetch_email_detail(self, message_id: str) -> Optional[Dict]:
        """
        Fetch detailed information for a single email.

        Args:
            message_id: Gmail message ID

        Returns:
            Dictionary with email data or None if error
        """
        try:
            message = self.service.users().messages().get(
                userId='me',
                id=message_id,
                format='full'
            ).execute()

            # Parse headers
            headers = {h['name']: h['value'] for h in message['payload']['headers']}

            # Extract body
            body_text, body_html = self._extract_body(message['payload'])

            # Parse email addresses
            sender = self._parse_email_address(headers.get('From', ''))
            recipients = self._parse_email_address(headers.get('To', ''))

            email_data = {
                'gmail_message_id': message_id,
                'gmail_thread_id': message.get('threadId'),
                'message_id': headers.get('Message-ID'),
                'in_reply_to': headers.get('In-Reply-To'),
                'references': headers.get('References'),
                'subject': headers.get('Subject', '(No Subject)'),
                'sender': sender,
                'recipients': recipients,
                'cc': self._parse_email_address(headers.get('Cc', '')),
                'bcc': self._parse_email_address(headers.get('Bcc', '')),
                'body_text': body_text,
                'body_html': body_html,
                'date': headers.get('Date'),
                'timestamp': datetime.fromtimestamp(int(message['internalDate']) / 1000),
                'labels': message.get('labelIds', []),
                'snippet': message.get('snippet', ''),
                'is_read': 'UNREAD' not in message.get('labelIds', [])
            }

            return email_data

        except HttpError as e:
            logger.error(f"Gmail API error fetching message {message_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error parsing message {message_id}: {e}")
            return None

    def _extract_body(self, payload: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Extract email body (text and HTML) from message payload.

        Args:
            payload: Email payload from Gmail API

        Returns:
            Tuple of (plain_text, html)
        """
        body_text = None
        body_html = None

        def extract_parts(parts):
            nonlocal body_text, body_html
            for part in parts:
                mime_type = part.get('mimeType')

                if mime_type == 'text/plain':
                    data = part['body'].get('data')
                    if data:
                        body_text = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

                elif mime_type == 'text/html':
                    data = part['body'].get('data')
                    if data:
                        body_html = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')

                elif mime_type.startswith('multipart/'):
                    if 'parts' in part:
                        extract_parts(part['parts'])

        # Handle different payload structures
        if 'parts' in payload:
            extract_parts(payload['parts'])
        else:
            # Single part message
            data = payload['body'].get('data')
            if data:
                decoded = base64.urlsafe_b64decode(data).decode('utf-8', errors='ignore')
                mime_type = payload.get('mimeType')
                if mime_type == 'text/plain':
                    body_text = decoded
                elif mime_type == 'text/html':
                    body_html = decoded

        return body_text, body_html

    def _parse_email_address(self, email_str: str) -> Dict[str, str]:
        """
        Parse email address with name.

        Args:
            email_str: Email string like "John Doe <john@example.com>"

        Returns:
            Dict with 'name' and 'email' keys
        """
        if not email_str:
            return {'name': None, 'email': None}

        # Match "Name <email@example.com>" or just "email@example.com"
        match = re.match(r'^(.+?)\s*<(.+?)>$', email_str)
        if match:
            name = match.group(1).strip('" ')
            email_addr = match.group(2).strip()
        else:
            name = None
            email_addr = email_str.strip()

        return {'name': name, 'email': email_addr}

    def mark_as_read(self, message_id: str) -> bool:
        """
        Mark an email as read.

        Args:
            message_id: Gmail message ID

        Returns:
            bool: True if successful
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            self.service.users().messages().modify(
                userId='me',
                id=message_id,
                body={'removeLabelIds': ['UNREAD']}
            ).execute()

            logger.info(f"Marked message {message_id} as read")
            return True

        except HttpError as e:
            logger.error(f"Error marking message as read: {e}")
            return False

    def send_reply(
        self,
        to: str,
        subject: str,
        body: str,
        in_reply_to: str = None,
        references: str = None,
        html: bool = False,
        thread_id: str = None
    ) -> Optional[str]:
        """
        Send a reply email.

        Args:
            to: Recipient email address
            subject: Email subject (should start with "Re:" for replies)
            body: Email body (text or HTML)
            in_reply_to: Message-ID being replied to
            references: References header for threading
            html: If True, send as HTML email
            thread_id: Gmail thread ID to continue conversation

        Returns:
            Message ID of sent email or None if failed
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Create message
            if html:
                message = MIMEMultipart('alternative')
                message.attach(MIMEText(body, 'html'))
            else:
                message = MIMEText(body)

            message['To'] = to
            message['From'] = self.user_email
            message['Subject'] = subject

            # Add threading headers
            if in_reply_to:
                message['In-Reply-To'] = in_reply_to
            if references:
                message['References'] = references

            # Encode message
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')

            # Send with thread ID if provided
            send_body = {'raw': raw_message}
            if thread_id:
                send_body['threadId'] = thread_id

            result = self.service.users().messages().send(
                userId='me',
                body=send_body
            ).execute()

            message_id = result.get('id')
            logger.info(f"Successfully sent reply to {to}, message_id: {message_id}")

            return message_id

        except HttpError as e:
            logger.error(f"Gmail API error sending reply: {e}")
            return None
        except Exception as e:
            logger.error(f"Error sending reply: {e}")
            return None

    def get_message_by_id(self, message_id: str) -> Optional[Dict]:
        """
        Get a specific message by Gmail message ID.

        Args:
            message_id: Gmail message ID

        Returns:
            Email data dictionary or None
        """
        return self._fetch_email_detail(message_id)

    def search_thread_by_message_id(self, message_id_header: str) -> Optional[str]:
        """
        Search for a Gmail thread by Message-ID header.

        Args:
            message_id_header: Email Message-ID header value

        Returns:
            Gmail thread ID or None if not found
        """
        if not self.service:
            raise RuntimeError("Not authenticated. Call authenticate() first.")

        try:
            # Clean message ID
            clean_id = message_id_header.strip('<>')

            # Search for message
            results = self.service.users().messages().list(
                userId='me',
                q=f'rfc822msgid:{clean_id}',
                maxResults=1
            ).execute()

            messages = results.get('messages', [])
            if messages:
                return messages[0].get('threadId')

            return None

        except HttpError as e:
            logger.error(f"Error searching for thread: {e}")
            return None
