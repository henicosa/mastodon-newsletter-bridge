import mail
import body

import os
import shutil

import argparse
from datetime import datetime

parser = argparse.ArgumentParser(description="Flip a switch by setting a flag")
parser.add_argument('-d', action='store_true')
parser.add_argument('-p', action='store_true')
parser.add_argument('-f', action='store_true')
parser.add_argument('-l', action='store_true')
parser.add_argument('-i', '--init', action='store_true', help='Initialize a new content file for a date range and fetch matching Mastodon articles')
parser.add_argument('-t', '--template', default='default', help='Template directory to use (for example: default or neo_full_frame)')
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

def generate_newsletter(local_linking=False, template_name='default'):
    body.generate_body(local_linking, template_name)
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

def generate(local_linking=False, template_name='default'):
    mail_content = generate_newsletter(local_linking, template_name)

def debug(use_english):
    mail_content = get_saved_content(use_english)
    mail.debug_newsletter(mail_content)

def fetch_articles():
    body.fetch_articles()


def ask_for_date(prompt_label):
    while True:
        value = input(prompt_label + " (dd.mm.yyyy): ")
        try:
            return datetime.strptime(value, "%d.%m.%Y").date()
        except ValueError:
            print("Ungültiges Datum. Bitte im Format tt.mm.jjjj eingeben.")


def initialize_content():
    content_dir = "content"
    os.makedirs(content_dir, exist_ok=True)
    content_file = os.path.join(content_dir, "content.md")

    if os.path.exists(content_file) and os.path.getsize(content_file) > 0:
        overwrite = input(f"{content_file} existiert bereits und enthält Inhalte. Überschreiben? [y/N]: ")
        if overwrite.strip().lower() not in ["y", "yes"]:
            print("Initialisierung abgebrochen.")
            return

    start = ask_for_date("Startdatum")
    end = ask_for_date("Enddatum")
    if end < start:
        print("Das Enddatum muss nach dem Startdatum liegen.")
        return

    title = input("Newsletter-Titel (optional): ").strip() or "Newsletter"
    issue_number = input("Ausgabenummer (optional): ").strip() or "1"

    default_intro_image = "![Ludwig genießt den längsten Sommer seines Lebens](resources/2024/sommer/author.jpg)"
    template = (
        f"---\n"
        f"start: {start.strftime('%d.%m.%Y')}\n"
        f"end: {end.strftime('%d.%m.%Y')}\n"
        f"---\n"
        f"# {title}\n"
        f"## {issue_number}\n"
        f"# Intro\n"
        f"{default_intro_image}\n\n"
        f"# Timeline\n"
    )
    with open(content_file, "w", encoding="utf-8") as fh:
        fh.write(template)

    print(f"Neue Inhaltsdatei wurde erstellt: {content_file}")
    fetch_articles()


if __name__=="__main__":
    args = parser.parse_args()
    if args.init:
        initialize_content()
    elif args.d:
        debug(args.e)
    elif args.p:
        publish(args.e)
    elif args.f:
        fetch_articles()
    else:
        #body.update_content_from_bridges(12)
        generate(args.l, args.template)