from __future__ import print_function
import os # library for interacting with the operating system
import pickle # library for serializing and deserializing Python objects

from google.auth.transport.requests import Request  # library for making HTTP requests
from google.oauth2.credentials import Credentials # library for handling OAuth 2.0 credentials
from google_auth_oauthlib.flow import InstalledAppFlow # library for handling OAuth 2.0 authorization flows
from googleapiclient.discovery import build # library for building Google API clients
from googleapiclient.errors import HttpError # library for handling HTTP errors from Google API clients

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']

def authenticate_gmail():
    
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)

    # Check if there are no (valid) credentials available
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # Start the OAuth 2.0 authorization flow to get new credentials
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            # Save the credentials for the next run
            token.write(creds.to_json())
            
    print("Authentication successful. Token saved to token.json")

    
    try:
        # Call the Gmail API
        service = build('gmail', 'v1', credentials=creds)
        #  Make a test API call to verify the service is working
        results = service.users().labels().list(userId='me').execute()
        # Get the list of labels
        labels = results.get('labels', [])
        print("Gmail service created successfully.")

    # Handle potential errors from the Gmail API
    except HttpError as error:
        print(f'An error occurred: {error}')

if __name__ == "__main__":
    authenticate_gmail()