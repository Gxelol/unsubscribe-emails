import requests
import json
import logging

from urllib.parse import urlparse

class UrlChecker:
    def __init__(self, api_key):
        self.api_key = api_key

    def check_url(self, url: str) -> bool:
        if url.startswith("<") and url.endswith(">"):
            url = url[1:-1]
        
        if not url.startswith("https://"):
            return False
        
        url_without_token = self._withdraw_token(url)
        return self._check_domain(url_without_token, self.api_key)

    def _withdraw_token(url: str) -> str:
        url_parts = urlparse(url)
        return f"{url_parts.scheme}://{url_parts.netloc}"

    def _check_domain(self, url: str) -> bool:
        api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={self.api_key}"
        headers = {
        'Content-Type': 'application/json',
        }
        body =   {
            "client": {"clientId": "Nothing","clientVersion": "1.5.2"},
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
                {"url": url},
            ]
            }
        }

        response = requests.post(api_url, headers=headers, data=json.dumps(body))

        if response.status_code == 200:
            result = response.json()
            if 'matches' in result:
                logging.warning(f"The URL {url} is listed as dangerous.")
                return False
            else:
                logging.info(f"The URL {url} is safe.")
                return True
        else:
            return {"error": f"Error: {response.status_code}, Message: {response.text}"}