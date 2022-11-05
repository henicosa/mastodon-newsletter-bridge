import mail
import body

import os
import shutil

def generate_newsletter():
    body.fetch_local_content()
    text = open("content/newsletter.txt", "r").read()
    html = open("content/newsletter.html", "r").read()
    return {"text": text, "html": html, "subject": "Ludwig's Interim-News"}

def archive_newsletter():
    src = r"content"
    dst = r"archive/" + mail_content["subject"]
    shutil.copytree(src, dst, dirs_exist_ok=False)
    src = r"templates"
    dst = r"archive/" + mail_content["subject"] + "/templates"
    shutil.copytree(src, dst, dirs_exist_ok=False)
    print("Newsletter-Dateien wurden erfolgreich archiviert.")

def publish():
    # generate mail content
    mail_content = generate_newsletter()
    
    # publish mail
    mail.publish_newsletter(mail_content)

    # store newsletter in archive
    archive_newsletter()


def debug():
    mail_content = generate_newsletter()
    # mail.debug_newsletter(mail_content)


if __name__=="__main__":
    debug()