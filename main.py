import asyncio
import logging

from unsubscribe_emails.auth import GmailAuthenticator
from unsubscribe_emails.emails import EmailProcessor

async def main():
    authenticator = GmailAuthenticator()
    creds = authenticator.authenticate_gmail()
    access_token = creds.token
    auth_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    email_processor = EmailProcessor(auth_headers)
    emails = await email_processor.fetch_emails()

    if not emails:
        logging.error("No emails retrieved from Gmail.")
        return

    await email_processor.process_messages(emails)

if __name__ == "__main__":
    asyncio.run(main())
 