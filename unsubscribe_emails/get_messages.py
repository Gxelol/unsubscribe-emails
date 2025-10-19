import requests
import re
import os
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

from auth import authenticate_gmail
from utils import check_url

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def list_messages():
    creds = authenticate_gmail()
    access_token = creds.token
    auth_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    messages = get_promotions_messages(auth_headers)
    messages_ids = [msg['id'] for msg in messages]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(fetch_message, id, auth_headers) for id in messages_ids]
        for future in as_completed(futures):
            id, res_message = future.result()

            if res_message.status_code != 200:
                log_message_error(id, res_message)
                continue
            process_message(id, res_message, auth_headers)

def get_promotions_messages(headers):
    url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages/?q=category:promotions'
    res_messages = requests.get(url.format(userId='me'), headers=headers)
    return res_messages.json().get("messages", [])

def fetch_message(id, headers):
    res_message = requests.get(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}?format=full', headers=headers)
    return id, res_message

def process_message(id, res_message, auth_header):
    payload = res_message.json().get("payload", {})
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
    res_delete = requests.delete(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}/', headers=auth_header)
    if res_delete.status_code == 200 or res_delete.status_code == 204:
        logging.info(f"Message ID {id} deleted successfully.\n\n")
        return id, res_delete
    else:
        logging.error(f"Failed to delete Message ID {id}. Status code: {res_delete.status_code}\n")
        return id, res_delete
    
def log_message_error(id, res_message):
    logging.error(f"Error when getting message {id}: {res_message.status_code} - {res_message.text}")

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
    list_messages()
 