from flask import render_template, url_for

import appname.constants as constants
from appname.mailers import Mailer
from appname.extensions import token

import os

class ConfirmEmail(Mailer):
    TEMPLATE = 'email/confirm_email.html'
    DEFAULT_SUBJECT = "Confirm your email on appname"

    def send(self):
        if self.recipient.email_confirmed:
            return False
        user_token = token.generate(
            self.recipient.email, salt=constants.EMAIL_CONFIRMATION_SALT)
        link = url_for('auth.confirm', code=user_token, _external=True)
        html_body = render_template(self.TEMPLATE, link=link)
        return self.deliver_later(self.recipient_email, self.subject, html_body)

class ResetPassword(Mailer):
    TEMPLATE = 'email/reset_password.html'

    def send(self, auth_token):
        link = f"{os.getenv('WEBSITE_URL')}/auth/reset-password/?token={auth_token}"
        html_body = render_template(self.TEMPLATE, link=link)
        to_emails=[self.recipient_email]
        subject="SFR Analytics Password Reset"

        return self.send_by_mailgun(to_emails=to_emails, subject=subject, html_body=html_body)
    
class WelcomeEmail(Mailer):
    TEMPLATE = 'email/welcome.html'

    def send(self):
        link = f"{os.getenv('WEBSITE_URL')}"
        html_body = render_template(self.TEMPLATE, link=link)
        to_emails=[self.recipient_email]
        subject="SFR Analytics Sign up Successful"

        return self.send_by_mailgun(to_emails=to_emails, subject=subject, html_body=html_body)