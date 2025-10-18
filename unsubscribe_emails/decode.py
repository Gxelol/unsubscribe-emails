import base64
import quopri

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
