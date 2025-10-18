import requests

from decode import decode_messages   
from auth import authenticate_gmail

def list_messages():
    # Authenticate and get access token
    creds = authenticate_gmail()
    access_token = creds.token
    url = 'https://gmail.googleapis.com/gmail/v1/users/{userId}/messages'
    headers = {
        'Authorization': f'Bearer {access_token}',
    }

    # Get the list of messages
    res_messages = requests.get(url.format(userId='me'), headers=headers)
    
    # Extract message IDs from the response
    messages = res_messages.json().get("messages", [])

    messages_ids = [msg['id'] for msg in messages]

    message = messages_ids[:1]
    
    res_message = requests.get(f'https://gmail.googleapis.com/gmail/v1/users/me/messages/{message[0]}', headers=headers)

    res_message_json = res_message.json()

    # Extract the message payload and decode the body
    payload = res_message_json.get("payload", {})
    parts = payload.get("parts", [])

    # Iterate through parts to find and decode the message body
    for part in parts:
        body = part.get("body", {})
        data = body.get("data", "")
        encoding = body.get("size", 0)

        # Get content transfer encoding
        if data and encoding:
            decoded_body = decode_messages(data, content_transfer_encoding=encoding)
            print(f'Decoded message body: {decoded_body}')

if __name__ == "__main__":
    list_messages()