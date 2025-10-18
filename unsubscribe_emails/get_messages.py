import requests
import re

from auth import authenticate_gmail
from utils import check_url

def list_messages():
    # Authenticate and get access token
    creds = authenticate_gmail()
    access_token = creds.token
    url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages/?q=category:promotions'
    auth_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    # Get the list of messages
    res_messages = requests.get(url.format(userId='me'), headers=auth_headers)
    
    # Extract message IDs from the response
    messages = res_messages.json().get("messages", [])

    messages_ids = [msg['id'] for msg in messages]

    three_first_ids = messages_ids[:3]

    print(f"Three first messages: {three_first_ids}\n\n")

    # Fetch and process each message
    for id in three_first_ids:
        
        res_message = requests.get(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{id}?format=full', headers=auth_headers)
        
        if res_message.status_code != 200:
            print(f"Erro ao buscar mensagens: {res_message.status_code} - {res_message.text}")
            return
        
        payload = res_message.json().get("payload", {})
        headers = payload.get("headers", [])
        list_unsubscribe = [header for header in headers if header["name"].lower() == "list-unsubscribe"]

        if list_unsubscribe:
            unsubscribe_header = list_unsubscribe[0]['value']
            match = re.search(r'<(https?://[^>]+)>', unsubscribe_header)

            if match:
                unsubscribe_link = [match.group(1)]
                is_safe = check_url(unsubscribe_link[0])
                if is_safe.get("success"):
                    print(f"Message ID: {id} - Unsubscribe link is safe: {is_safe['success']}\n\n")
                else:
                    print(f"Warning: {is_safe['error']}\n\n")
            else:
                print("Unsubscribe link not found.")
        else:
            print(f"Message ID: {id} has no List-Unsubscribe header.\n\n")



if __name__ == "__main__":
    list_messages()