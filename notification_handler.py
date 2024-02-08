from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')


TWILIO_SID=os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN=os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_VIRTUAL_NUMBER=os.getenv("TWILIO_PHONE_NUMBER")
TWILIO_VERIFIED_NUMBER=os.getenv("TWILIO_VERIFIED_NUMBER")
TWILIO_WHATSAPP_NUMBER=os.getenv("TWILIO_WHATSAPP_NUMBER")

class NotificationHandler:
    def __init__(self):
        self.client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    def send_sms(self, message):
        message = self.client.messages \
            .create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}',
            body=message,
            to=f'whatsapp:{TWILIO_VERIFIED_NUMBER}'
        )

        print(f'\nWhatsApp notification sent successfully: {message.sid}')