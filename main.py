import mail
import body

import os
import shutil

import argparse

parser = argparse.ArgumentParser(description="Flip a switch by setting a flag")
parser.add_argument('-d', action='store_true')
parser.add_argument('-p', action='store_true')

def get_saved_content():
    text = open("content/newsletter.txt", "r").read()
    html = open("content/newsletter.html", "r").read()
    return {"text": text, "html": html, "subject": "Ludwig's Kanada-Kurier"}

def generate_newsletter():
    body.generate_body()
    text = open("content/newsletter.txt", "r").read()
    html = open("content/newsletter.html", "r").read()
    return {"text": text, "html": html, "subject": "Ludwig's Kanada-Kurier"}

def archive_newsletter(mail_content):
    src = r"content"
    dst = r"archive/" + mail_content["subject"]
    shutil.copytree(src, dst, dirs_exist_ok=False)
    src = r"templates"
    dst = r"archive/" + mail_content["subject"] + "/templates"
    shutil.copytree(src, dst, dirs_exist_ok=False)
    print("Newsletter-Dateien wurden erfolgreich archiviert.")

def publish():
    # generate mail content
    mail_content = get_saved_content()
    
    # publish mail
    # mail.publish_newsletter(mail_content)

    # store newsletter in archive
    archive_newsletter(mail_content)

def generate():
    mail_content = generate_newsletter()

def debug():
    mail_content = get_saved_content()
    mail.debug_newsletter(mail_content)


if __name__=="__main__":
    args = parser.parse_args()
    if args.d:
        debug()
    elif args.p:
        publish()
    else:
        generate()