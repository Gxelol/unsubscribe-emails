import asyncio
import logging

from unsubscribe_emails.auth import authenticate_gmail
from unsubscribe_emails.emails import fetch_message_async, get_promotions_messages, log_message_error, process_message

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def main():
    creds = authenticate_gmail()
    access_token = creds.token
    auth_headers = {
        'Authorization': f'Bearer {access_token}',
    }

    emails = await get_promotions_messages(auth_headers)

    if not emails:
        logging.error("No emails retrieved from Gmail.")
        return

    emails_ids = [email['id'] for email in emails]

    tasks = []

    for id in emails_ids:
        tasks.append(fetch_message_async(id, auth_headers))

    results = await asyncio.gather(*tasks)

    for id, res_message in results:
        if res_message is None:
            logging.warning(f"Skipping message {id} due to timeout or error.")
            continue

        if res_message.status == 200:
            await process_message(id, res_message, auth_headers)
        else:
            log_message_error(id, res_message)

if __name__ == "__main__":
    asyncio.run(main())
 