import requests
import json
import logging

from urllib.parse import urlparse

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_url(url: str, api_key: str) -> dict:
    if url.startswith("<") and url.endswith(">"):
        url = url[1:-1]
    
    if not url.startswith("https://"):
        return {"error": "Only secure URLs (https) are supported"}
    
    url_without_token = withdraw_token(url)
    return check_domain(url_without_token, api_key)

def withdraw_token(url: str) -> str:
    url_parts = urlparse(url)
    return f"{url_parts.scheme}://{url_parts.netloc}"

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