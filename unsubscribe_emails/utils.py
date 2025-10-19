import base64
import quopri
import requests
import json
import logging

from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# def decode_messages(data_base64: str, content_transfer_encoding: str = "base64") -> str:
#     # Decode the message body based on the content transfer encoding
#     if content_transfer_encoding == "quoted-printable":
        
#         # Decode quoted-printable
#         quoted_decoded = quopri.decodestring(data_base64)
#         return quoted_decoded.decode("utf-8", errors="replace")

#     # Base64 decoding
#     base64_bytes = data_base64.encode("utf-8")
#     decoded_bytes = base64.urlsafe_b64decode(base64_bytes + b'==')
#     return decoded_bytes.decode("utf-8", errors="replace")

def check_url(url: str, api_key: str) -> dict:
    if url.startswith("<") and url.endswith(">"):
        url = url[1:-1]
    
    if url.startswith("http://"):
        return False
    elif url.startswith("https://"):
        url_without_token = withdraw_token(url)
        return check_domain(url_without_token, api_key)
    else:
        return {"error": "URL not suported"}

def withdraw_token(url: str) -> str:
    url_parts = urlparse(url)
    domain = url_parts.netloc
    https = url_parts.scheme
    new_url = https + '://' + domain
    return new_url

def check_domain(urls: list, api_key: str) -> bool:
    url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"

    headers = {
    'Content-Type': 'application/json',
    }


    body =   {
        "client": {
        "clientId": "Nothing",
        "clientVersion": "1.5.2"
        },
        "threatInfo": {
        "threatTypes": [
            "MALWARE", 
            "SOCIAL_ENGINEERING", 
            "UNWANTED_SOFTWARE", 
            "POTENTIALLY_HARMFUL_APPLICATION"
        ],
        "platformTypes":    ["WINDOWS", "LINUX", "ANDROID"],
        "threatEntryTypes": ["URL", "EXECUTABLE"],
        "threatEntries": [
            {"url": urls},
        ]
        }
    }

    response = requests.post(url, headers=headers, data=json.dumps(body))

    if response.status_code == 200:
        result = response.json()
        if 'matches' in result:
            logging.warning(f"The URL {urls} is listed as dangerous.")
            return False
        else:
            logging.info(f"The URL {urls} is safe.")
            return True
    else:
        return {"error": f"Error: {response.status_code}, Message: {response.text}"}