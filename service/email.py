from flask_mail import Message
from flask import render_template
from service import mail
from service import app
from threading import Thread


def send_async_email(app, msg):
    with app.app_context():
        mail.send(msg)


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email, args=(app, msg)).start()


def send_invite_email(emails, host_name, group_name, close_date):
    send_email('Secret Santa Invitation!',
               sender=app.config['ADMINS'][0],
               recipients=emails,
               text_body=render_template('emails/invitation.txt',
                                         host_name=host_name, group_name=group_name,
                                         close_date=close_date),
               html_body=render_template('emails/invitation.html',
                                         host_name=host_name, group_name=group_name,
                                         close_date=close_date))


def send_reveal_email(email, group_name, santa, preference_first, preference_second, preference_third):
    send_email('Ready to be Santa? Come find out!',
               sender=app.config['ADMINS'][0],
               recipients=[email],
               text_body=render_template('emails/reveal.txt', group_name=group_name, santa=santa,
                                         preference_first=preference_first, preference_second=preference_second,
                                         preference_third=preference_third),
               html_body=render_template('emails/reveal.html', group_name=group_name, santa=santa,
                                         preference_first=preference_first, preference_second=preference_second,
                                         preference_third=preference_third
                                         ))