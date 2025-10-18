import requests
import os
import base64

from auth import authenticate_gmail

def list_messages():
    creds = authenticate_gmail()
    access_token = creds.token
    url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    res_messages = requests.get(url.format(userId='me'), headers=headers)

    messages = res_messages.json().get("messages", [])

    messages_ids = [msg['id'] for msg in messages]

    first_1_id = messages_ids[:1]
    
    for msg_id in first_1_id:
        res_message = requests.get(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{msg_id}', headers=headers)

        print(f'Messages: {res_message.json()}')
    

if __name__ == "__main__":
    list_messages()