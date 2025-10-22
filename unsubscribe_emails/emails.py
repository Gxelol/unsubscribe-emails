import requests
import logging
import aiohttp
import asyncio
import random
import time
import re
import os

semaphore = asyncio.Semaphore(10)

from unsubscribe_emails.utils import check_url

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def get_promotions_messages(headers):
    url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages/?q=category:promotions'
    messages = []
    next_page_token = None

    async with aiohttp.ClientSession() as session:
        while True:
            data = await fetch_messages_page(session, url.format(userId='me'), headers, next_page_token)
            if not data:
                break

            messages.extend(data.get("messages", []))
            next_page_token = data.get("nextPageToken")

            if not next_page_token:
                break

    return messages

async def fetch_messages_page(session, url, headers, next_page_token=None):
    params = {'pageToken': next_page_token} if next_page_token else {}
    async with session.get(url, headers=headers, params=params) as res_messages:
        if res_messages.status == 200:
            data = await res_messages.json()
            return data
        else:
            logging.error(f"Failed to retrieve messages: {res_messages.status}")
            return None

async def fetch_message_async(id, headers, timeout=10):
    url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}?format=full'

    try:
        async with aiohttp.ClientSession() as session:
            res = await asyncio.wait_for(session.get(url, headers=headers), timeout=timeout)
            return id, res
    except Exception as e:
        await handle_request_error(e, id)
        return id, None
    
async def process_message(id, res_message, auth_header):
    async with semaphore:
        payload = {}
        
        try:
            payload = await res_message.json()
            payload = payload.get("payload", [])
        except aiohttp.ClientConnectionError as e:
            logging.error(f"Connection error when processing message {id}: {e}")
        except Exception as e:
            logging.error(f"Error when processing message {id}: {e}")
        
        headers = payload.get("headers", [])
        list_unsubscribe = get_list_unsubscribe(headers)

        if list_unsubscribe:
            unsubscribe_link = extract_unsubscribe_link(list_unsubscribe)
            if unsubscribe_link:
                handle_unsubscribe_link(id, unsubscribe_link, auth_header)
            else:
                logging.warning(f"Unsubscribe link not found in message ID: {id}")
                delete_message(id, auth_header)
        else:
            logging.info(f"Message ID: {id} has no List-Unsubscribe header.")
            delete_message(id, auth_header)

def delete_message(id, auth_header):
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
    
def log_message_error(id, res_message):
    logging.error(f"Error when getting message {id}: {res_message.status} - {res_message.text}")

async def handle_request_error(exception, id=None):
    if isinstance(exception, asyncio.TimeoutError):
        logging.warning(f"Timeout occurred while fetching message {id}. Skipping this message.")
    elif isinstance(exception, aiohttp.ClientConnectionError):
        logging.error(f"Connection error when fetching message {id}: {exception}")
    else:
        logging.error(f"Unexpected error: {exception}")

def get_list_unsubscribe(headers):
    return [header for header in headers if header["name"].lower() == "list-unsubscribe"]

def extract_unsubscribe_link(list_unsubscribe):
    unsubscribe_header = list_unsubscribe[0]['value']
    match = re.search(r'<(https?://[^>]+)>', unsubscribe_header)
    return match.group(1) if match else None

def handle_unsubscribe_link(id, unsubscribe_link, auth_header):
    safe_browsing_api = os.getenv('SAFE_BROWSING_API')
    is_safe = check_url(unsubscribe_link, safe_browsing_api)

    if is_safe is True:
        logging.info(f"Message ID: {id} - Unsubscribe link is safe")
        try:
            requests.get(unsubscribe_link)
            delete_message(id, auth_header)
        except Exception as e:
            logging.error(f"Exception when unsubscribing/deleting message {id}: {e}")
    elif is_safe is False:
        logging.warning(f"Warning: The URL is dangerous\n\n")
    else: 
        logging.error(f"Error: {is_safe['error']}")
