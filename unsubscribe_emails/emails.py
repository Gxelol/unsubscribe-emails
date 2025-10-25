import requests
import logging
import aiohttp
import asyncio
import re
import os

from unsubscribe_emails.utils import UrlChecker

class EmailProcessor:
    def __init__(self, auth_header):
        self.auth_header = auth_header
        self.semaphore   = asyncio.Semaphore(10)

    async def fetch_emails(self):
        url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages/?q=category:promotions'
        messages = []
        next_page_token = None

        async with aiohttp.ClientSession() as session:
            while True:
                data = await self._fetch_email_pages(session, url.format(userId='me'), next_page_token)
                if not data:
                    break

                messages.extend(data.get("messages", []))
                next_page_token = data.get("nextPageToken")

                if not next_page_token:
                    break
        return messages

    async def _fetch_email_pages(self, session, url, next_page_token=None):
        params = {'pageToken': next_page_token} if next_page_token else {}
        async with session.get(url, headers=self.auth_header, params=params) as res_messages:
            if res_messages.status == 200:
                data = await res_messages.json()
                return data
            else:
                logging.error(f"Failed to retrieve messages: {res_messages.status}")
                return None
            
    async def process_messages(self, emails):
        tasks = []
        for email in emails:
            tasks.append(self._process_message(email))
        await asyncio.gather(*tasks)

    async def _process_message(self, email):
        async with self.semaphore:
            try:
                res_message = await self._fetch_message_async(email['id'])
                if res_message and res_message.status == 200:
                    await self._handle_message(email['id'], res_message)
                else:
                    logging.warning(f"Skipping message {email['id']} due to error or timeout.")
            except Exception as e:
                logging.error(f"Error processing message {email['id']}: {e}")

    async def _fetch_message_async(self, id):
        url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}?format=full'

        try:
            async with aiohttp.ClientSession() as session:
                res = await session.get(url, headers=self.auth_header)
                return res
        except Exception as e:
            logging.error(f"Error fetching message {id}: {e}")
            return None
        
    async def _handle_message(self, id, res_message):
        payload = await res_message.json()
        headers = payload.get("payload", {}).get("headers", [])
        unsubscribe_header = next((h for h in headers if h['name'].lower == 'list-unsubscribe'), None)     

        if unsubscribe_header:
            unsubscribe_link = self._extract_unsubscribe_link(unsubscribe_header)
            if unsubscribe_link:
                await self._unsubscribe_and_delete(id, unsubscribe_link)
            else:
                logging.warning(f"Unsubscribe link not found in message ID: {id}")
                await self._delete_email(id)
        else:
            logging.info(f"Message ID: {id} has no List-Unsubscribe header.")
            self._delete_email(id)

    def _extract_unsubscribe_link(unsubscribe_header):
        match = re.search(r'<(https?://[^>]+)>', unsubscribe_header['value'])
        return match.group(1) if match else None
    

    async def _unsubscribe_and_delete(self, id, unsubscribe_link):
        if self.is_safe_url(unsubscribe_link):
            try:
                requests.get(unsubscribe_link)
                await self._delete_email(id)
            except Exception as e:
                logging.error(f"Exception when unsubscribing/deleting message {id}: {e}")
        else:
            logging.warning(f"Warning: The URL is dangerous\n\n")

    async def _is_safe_url(self, url):
        safe_browsing_api = os.getenv('SAFE_BROWSING_API')
        return UrlChecker.check_url(url, safe_browsing_api) is True

    async def _delete_email(id, auth_header):
        try:
            res_delete = requests.delete(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}/', headers=auth_header)
        except Exception as e:
            logging.error(f"Error when processing message {id}: {e}")
        
        if res_delete.status_code in [200, 204]:
            logging.info(f"Message ID {id} deleted successfully.\n\n")
            return id, res_delete
        else:
            logging.error(f"Failed to delete Message ID {id}. Status code: {res_delete.status_code}\n")
            return id, res_delete

