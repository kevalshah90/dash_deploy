import sendgrid
import os
from sendgrid.helpers.mail import *
from .models import PassRecovery, EmailVerification
from . import db
import random
from datetime import datetime

def sendMail(email_to):
    # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    sg = sendgrid.SendGridAPIClient(api_key='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')
    from_email = Email("info@stroomcre.com")
    to_email = To(email_to)
    subject = "Stroom App : Reset password"
    token = createTokenForRecovery(email_to)
    # content = Content("text/plain", "Your password is 123")

    # localhost
    # html_content= Content("text/html","<strong>Please click below link to reset password :</strong><br/><br/><a href='http://localhost:8000/updatePassword/"+token+"'>Reset Password</a>")

    # production
    html_content= Content("text/html","<strong>Please click below link to reset password :</strong><br/><br/><a href='https://application.stroomcre.com/updatePassword/"+token+"'>Reset Password</a>")

    mail = Mail(from_email, to_email, subject, html_content)
    response = sg.client.mail.send.post(request_body=mail.get())

def sendMailForVerification(email_to):
    # sg = sendgrid.SendGridAPIClient(api_key=os.environ.get('SENDGRID_API_KEY'))
    sg = sendgrid.SendGridAPIClient(api_key='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')
    from_email = Email("info@stroomcre.com")
    to_email = To(email_to)
    subject = "Stroom App : Email Verification"
    token = createTokenForEmailVerification(email_to)
    # content = Content("text/plain", "Your password is 123")

    # localhost
    # html_content= Content("text/html","<strong>Please click below link to verify your email address :</strong><br/><br/><a href='http://localhost:8000/verifyEmail/"+token+"'>Verify Email</a>")

    # production
    html_content= Content("text/html","<strong>Please click below link to verify your email address :</strong><br/><br/><a href='https://application.stroomcre.com/verifyEmail/"+token+"'>Verify Email</a>")

    mail = Mail(from_email, to_email, subject, html_content)
    response = sg.client.mail.send.post(request_body=mail.get())

def createTokenForRecovery(email):
    random_string = ''

    for _ in range(10):
        # Considering only upper and lowercase letters
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
        # Convert to lowercase if the flip bit is on
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
        # Keep appending random characters using chr(x)
        random_string += (chr(random_integer))

    pass_recovery = PassRecovery(email=email, token=random_string, status=0,created=datetime.now())

    # add the new user to the database
    db.session.add(pass_recovery)
    db.session.commit()
    return random_string

def createTokenForEmailVerification(email):
    random_string = ''

    for _ in range(10):
        # Considering only upper and lowercase letters
        random_integer = random.randint(97, 97 + 26 - 1)
        flip_bit = random.randint(0, 1)
        # Convert to lowercase if the flip bit is on
        random_integer = random_integer - 32 if flip_bit == 1 else random_integer
        # Keep appending random characters using chr(x)
        random_string += (chr(random_integer))

    pass_verification = EmailVerification(email=email, token=random_string, status=0,created=datetime.now())

    # add the new user to the database
    db.session.add(pass_verification)
    db.session.commit()
    return random_string
