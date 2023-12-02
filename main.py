import mail
import body

import os
import shutil

import argparse

parser = argparse.ArgumentParser(description="Flip a switch by setting a flag")
parser.add_argument('-d', action='store_true')
parser.add_argument('-p', action='store_true')
parser.add_argument('-l', action='store_true')
# process english version
parser.add_argument('-e', action='store_true')

def get_saved_content(use_english):
    news_filename = "newsletter"
    if use_english:
        news_filename = "en"
    text = open("content/newsletter.txt", "r").read()
    html = open("content/" + news_filename + ".html", "r").read()

    # automatic subject detection
    return {"text": text, "html": html, "subject": body.get_title(use_english)}

def generate_newsletter(local_linking=False):
    body.generate_body(local_linking)
    text = open("content/newsletter.txt", "r").read()
    html = open("content/newsletter.html", "r").read()
    
    return {"text": text, "html": html, "subject":body.get_title()}

def archive_newsletter(mail_content):
    src = r"content"
    dst = r"archive/" + mail_content["subject"]
    shutil.copytree(src, dst, dirs_exist_ok=False)
    src = r"templates"
    dst = r"archive/" + mail_content["subject"] + "/templates"
    shutil.copytree(src, dst, dirs_exist_ok=False)
    print("Newsletter-Dateien wurden erfolgreich archiviert.")

def publish(use_english):
    # generate mail content
    mail_content = get_saved_content(use_english)
    
    # publish mail
    mail.publish_newsletter(mail_content, use_english)

    # store newsletter in archive
    archive_newsletter(mail_content)

def generate(local_linking=False):
    mail_content = generate_newsletter(local_linking)

def debug(use_english):
    mail_content = get_saved_content(use_english)
    mail.debug_newsletter(mail_content)


if __name__=="__main__":
    args = parser.parse_args()
    if args.d:
        debug(args.e)
    elif args.p:
        publish(args.e)
    else:
        #body.update_content_from_bridges(12)
        generate(args.l)