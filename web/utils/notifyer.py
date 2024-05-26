from threading import Thread
import traceback
from flask import current_app, jsonify, render_template, request
from flask_mail import Message
from web.extensions import mail
from web.apis.tokens import hash_auth

from dotenv import load_dotenv
from os import getenv
load_dotenv()

""" How to use my hash_auth lib """
#hash_it = hash_auth.hash_it(2) #make a hash
#unhash_it = hash_auth.unhash_it(hash_it) #reverse the hash

def send_async_email(app, msg):
    try:
        with app.app_context():
            mail.send(msg)
            print(f'sucess, email sent!')
            return True
    except Exception as e:
        print(f"email-failure->{traceback.print_exc()}")
        print(f"failure in sending email ->{e} |, {getenv('mail_username')}, {getenv('mail_password')} ")
        return False

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.html = html_body
    msg.body = text_body
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def reset_email(user):
    #token = user.generate_token(type='reset')
    token = hash_auth.hash_it(user.id)
    send_email(
        ('[Russiantechnologies] . Reset Your Password'),
        sender=getenv('mail_username'),
        recipients=[user.email],
        text_body=render_template('email/forgot.txt', user=user, token=token),
        html_body=render_template('email/forgot.html', user=user, token=token)
               )

def verify_email(user):
    token = hash_auth.hash_it(user.id)
    send_email(
        ('[Russiantechnologies] . Salesnet Verifications'),
        sender=getenv('mail_username'),
        recipients=[user.email],
        text_body=render_template('email/verify.txt', user=user, token=token),
        html_body=render_template('email/verify.html', user=user, token=token)
               )
    
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from twilio.rest import Client
class TwilioHelper:
    def __init__(self, account_sid=getenv('my_twillo_sid'), auth_token=getenv('my_twillo_auth_token')):
        self.client = Client(account_sid, auth_token )

    def send_async_sms(self, to_phone_number, message):
        try:
            message = self.client.messages.create(
                body=message,
                from_=getenv('my_twillo_phone'),
                to=to_phone_number
            )
            return True, message.sid
        except TwilioRestException as e:
            print(f"SMS failure: {e}")
            return False
        except Exception as e:
            print(f"error sending sms with twillo{e}")
            return False, str(e)
    
    def send_sms(self, recipient, message_body):
        Thread(target=self.send_async_sms, args=(recipient, message_body)).start()

#twilio_helper = TwilioHelper(getenv('my_twillo_sid'), getenv('my_twillo_auth_token'))
#twilio_helper = TwilioHelper()

""" def send_sms(recipient, message_body):
    Thread(target=twilio_helper.send_async_sms, args=(recipient, message_body)).start()
 """

#SAMPLE USAGE:
""" @current_app.route("/send_order_confirmation", methods=["POST"])
def send_order_confirmation():
    data = request.get_json()
    phone_number = data.get("phone_number")
    order_id = data.get("order_id")

    message = f"Thank you for your order! Your order ID is {order_id}."
    
    success, response = twilio_helper.send_sms(phone_number, message)

    if success:
        return jsonify({"message": "Order confirmation SMS sent successfully."})
    else:
        return jsonify({"error": response}), 500 """
    
""" # Twilio Account SID and Auth Token
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'  # e.g., +1234567890
# Create a Twilio client
twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
def send_async_sms(recipient, message_body):
    try:
        # Send SMS
        twilio_client.messages.create(
            body=message_body,
            from_=TWILIO_PHONE_NUMBER,
            to=recipient
        )
        print('Success, SMS sent!')
        return True
    except TwilioRestException as e:
        print(f"SMS failure: {e}")
        return False
def send_sms(recipient, message_body):
    Thread(target=send_async_sms, args=(recipient, message_body)).start() """
