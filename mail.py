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
    contacts_file = open(filepath, "r").readlines()
    for line in contacts_file:
        if "#" != line[0] and "" != line[0]:
            line = line.replace("\n", "")
            line = line.split(" ")
            contacts.append({"email": line[0], "name": line[1]})
    return contacts


def publish_newsletter(mail_content:dict, use_english:bool=False) -> None:
    """Sends the newsletter to all subscribers in the file "secrets/subscribers.txt"
    
    Arguments:
        mail_content {dict} -- The content of the mail. Contains the subject, the text and the html version of the mail.
        use_english {bool} -- If true, the newsletter will be sent in english. If false, it will be sent in german.
    """

    subscribers_filename = "subscribers"
    

    if use_english:
        print("Sende Newsletter auf Englisch")
        subscribers_filename = "subscribers_en"
    else: 
        print("Sende Newsletter auf Deutsch")
    contacts = read_subscriptions("secrets/" + subscribers_filename + ".txt")

    for contact in contacts:
       send_mail(contact, mail_content)

def personalize_mail(mail_content, name):
    mail_content["text"] = mail_content["text"].replace("[insert reader name]", name)
    mail_content["html"] = mail_content["html"].replace("[insert reader name]", name)
    return mail_content

def debug_newsletter(mail_content):
    receiver = {"name": secrets["debug-receiver"]["name"], "email": secrets["debug-receiver"]["email"]}
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

    name = receiver["name"]
    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(mail_content["text"].replace("[insert reader name]", name), "plain")
    part2 = MIMEText(mail_content["html"].replace("[insert reader name]", name), "html")

    message.attach(part1)
    message.attach(part2)

    with smtplib.SMTP_SSL(secrets["sender"]["server-domain"], port, context=context) as server:
        server.login(secrets["sender"]["email"], password)
        server.sendmail(secrets["sender"]["email"], receiver["email"], message.as_string())
        print("E-Mail erfolgreich gesendet an " + receiver["name"])