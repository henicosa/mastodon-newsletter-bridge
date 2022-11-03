import email, smtplib, ssl

from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import json


def read_secrets():
    return json.load(open('secrets/secrets.json', 'r'))

secrets = read_secrets()


def read_subscriptions(filepath):
    contacts = []
    contacts_file = open("secrets/subscribers.txt", "r").read()
    for line in contacts_file:
        if "#" != line[0]:
            line = line.replace("\n", "")
            line = line.split(" ")
            contacts.append({"email": line[0], "name": line[1]})
    return contacts


def publish_newsletter(mail_content):
    contacts = []
    for contact in contacts:
        # replace name
        mail_content["text"] = mail_content["text"].replace("[receiver name]", contact["name"])
        mail_content["html"] = mail_content["html"].replace("[receiver name]", contact["name"])

        send_mail(contact, mail_content)


def debug_newsletter(mail_content):
    receiver = {"name": secrets["debug-receiver"]["name"], "email": secrets["debug-receiver"]["email"]}
    # replace name
    mail_content["text"] = mail_content["text"].replace("[receiver name]", secrets["debug-receiver"]["name"])
    mail_content["html"] = mail_content["html"].replace("[receiver name]", secrets["debug-receiver"]["name"])
    mail_content["subject"] = "Ludwig's Debug-News"
    send_mail(receiver, mail_content)


def send_mail(receiver, mail_content):
    port =  secrets["sender"]["server-port"] # For SSL 465
    password = secrets["sender"]["password"]

    # Create a secure SSL context
    context = ssl.create_default_context()

    message = MIMEMultipart("alternative")
    message["Subject"] = mail_content["subject"]
    message["From"] = secrets["sender"]["email"]
    message["To"] = receiver["email"]

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(mail_content["text"], "plain")
    part2 = MIMEText(mail_content["html"], "html")

    message.attach(part1)
    message.attach(part2)

    with smtplib.SMTP_SSL(secrets["sender"]["server-domain"], port, context=context) as server:
        server.login(secrets["sender"]["email"], password)
        server.sendmail(secrets["sender"]["email"], receiver["email"], message.as_string())
        print("E-Mail erfolgreich gesendet an " + receiver["name"])