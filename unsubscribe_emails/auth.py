import os # library for interacting with the operating system

from google.auth.transport.requests import Request  # library for making HTTP requests
from google.oauth2.credentials import Credentials # library for handling OAuth 2.0 credentials
from google_auth_oauthlib.flow import InstalledAppFlow # library for handling OAuth 2.0 authorization flows

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
            flow = InstalledAppFlow.from_client_secrets_file('../credentials/credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            # Save the credentials for the next run
            token.write(creds.to_json())
            
    print("Authentication successful. Token saved to token.json")
    return creds