from twilio.rest import Client
import os
from dotenv import load_dotenv
load_dotenv(dotenv_path='.env')


TWILIO_SID=os.environ["TWILIO_ACCOUNT_SID"]
TWILIO_AUTH_TOKEN=os.environ["TWILIO_AUTH_TOKEN"]
TWILIO_VIRTUAL_NUMBER="+441223658283"
TWILIO_VERIFIED_NUMBER="+447459555061"

class NotificationHandler:
    def __init__(self):
        self.client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)

    def send_sms(self, message):
        message = self.client.messages \
            .create(
            from_='whatsapp:+14155238886',
            body=message,
            to='whatsapp:+447459555061'
        )

        print(f'\nWhatsApp notification sent successfully: {message.sid}')