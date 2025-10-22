import requests
import re
import os
import logging
import aiohttp
import asyncio

# TRATAR A TRATAÇÃO DE ERRO REPETIDA CRIANDO UMA FUNÇÃO

from auth import authenticate_gmail
from utils import check_url

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def list_messages():
    creds = authenticate_gmail()
    access_token = creds.token
    auth_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    messages = await get_promotions_messages(auth_headers)

    if not messages:
        logging.error("No messages retrieved from Gmail.")
        return

    messages_ids = [msg['id'] for msg in messages]

    tasks = []

    for id in messages_ids:
        tasks.append(fetch_message_async(id, auth_headers))

    results = await asyncio.gather(*tasks)

    for id, res_message in results:
        if res_message is None:
            logging.warning(f"Skipping message {id} due to timeout or error.")
            continue

        if res_message.status == 200:
            await process_message(id, res_message, auth_headers)
        else:
            log_message_error(id, res_message)

async def get_promotions_messages(headers):
    url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages/?q=category:promotions'
    messages = []
    next_page_token = None

    async with aiohttp.ClientSession() as session:
        while True:
            try:
                if next_page_token:
                    async with session.get(url.format(userId='me') + f"&pageToken={next_page_token}", headers=headers) as res_messages:
                        if res_messages.status == 200:
                            data = await res_messages.json()
                            messages.extend(data.get("messages", []))
                            next_page_token = data.get("nextPageToken")
                            print(f"Token: {res_messages}")

                            if not next_page_token:
                                return messages
                        else:    
                            logging.error(f"Failed to retrieve messages: {res_messages.status_code}")
                            break
                else:
                    async with session.get(url.format(userId='me'), headers=headers) as res_messages:
                        if res_messages.status == 200:
                            data = await res_messages.json()
                            messages.extend(data.get("messages", []))
                            next_page_token = data.get("nextPageToken")

                            if not next_page_token:
                                return messages
                        else:
                            logging.error(f"Failed to retrieve messages: {res_messages.status}")
                            break
            except Exception as e:
                logging.error(f"Exception while retrieving messages: {str(e)}")
                return []

async def fetch_message_async(id, headers, timeout=10):
    url = f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}?format=full'

    try:
        async with aiohttp.ClientSession() as session:
            res = await asyncio.wait_for(session.get(url, headers=headers), timeout=timeout)
            return id, res
    except asyncio.TimeoutError:
        logging.warning(f"Timeout occurred while fetching message {id}. Skipping this message.")
        return id, None
    except aiohttp.ClientConnectionError as e:
        logging.error(f"Connection error when fetching message {id}: {e}")
        return id, None
    except Exception as e:
        logging.error(f"Unexpected error when fetching message {id}: {e}")
        return id, None

async def process_message(id, res_message, auth_header):
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
    except aiohttp.ClientConnectionError as e:
        logging.error(f"Connection error when processing message {id}: {e}")
    except Exception as e:
        logging.error(f"Error when processing message {id}: {e}")
    
    if res_delete.status_code == 200 or res_delete.status_code == 204:
        logging.info(f"Message ID {id} deleted successfully.\n\n")
        return id, res_delete
    else:
        logging.error(f"Failed to delete Message ID {id}. Status code: {res_delete.status_code}\n")
        return id, res_delete
    
def log_message_error(id, res_message):
    logging.error(f"Error when getting message {id}: {res_message.status} - {res_message.text}")

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

if __name__ == "__main__":
    asyncio.run(list_messages())
 