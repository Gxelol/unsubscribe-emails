import base64
import quopri
from urllib.parse import urlparse
import requests

def decode_messages(data_base64: str, content_transfer_encoding: str = "base64") -> str:
    # Decode the message body based on the content transfer encoding
    if content_transfer_encoding == "quoted-printable":
        
        # Decode quoted-printable
        quoted_decoded = quopri.decodestring(data_base64)
        return quoted_decoded.decode("utf-8", errors="replace")

    # Base64 decoding
    base64_bytes = data_base64.encode("utf-8")
    decoded_bytes = base64.urlsafe_b64decode(base64_bytes + b'==')
    return decoded_bytes.decode("utf-8", errors="replace")

def check_url(url: str) -> dict:
    if url.startswith("<") and url.endswith(">"):
        url = url[1:-1]
    
    if url.startswith("http://"):
        return {"error": "Insecure URL (http)"}
    elif url.startswith("https://"):
        extract_domain(url)
        return {"success": "Secure URL, the token was extracted"}
    else:
        return {"error": "Invalid URL format"}

def extract_domain(url: str) -> str:
    url_parts = urlparse(url)
    domain = url_parts.netloc
    return domain

def check_domain(url: str) -> dict:
    api_key = "YOUR_VIRUSTOTAL_API_KEY"
    headers = {
        "x-apikey": api_key
    }
    response = requests.get(f"https://www.virustotal.com/api/v3/domains/{url}", headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Failed to check URL in VirusTotal"}