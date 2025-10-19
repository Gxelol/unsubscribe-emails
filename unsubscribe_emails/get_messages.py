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

if __name__ == "__main__":
    list_messages()