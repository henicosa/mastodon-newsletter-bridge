import os
import bridges.local
import bridges.mastodon
import markdown
import datetime
import pprint
from bs4 import BeautifulSoup
import re
import hashlib

import json
def read_usernames():
    return json.load(open('secrets/usernames.json', 'r'))
usernames = read_usernames()

pp = pprint.PrettyPrinter(indent=2, width=530, compact=True)

DEFAULT_TEMPLATE_NAME = "default"


def resolve_template_dir(template_name="default"):
    candidate = os.path.join("templates", template_name)
    if os.path.isdir(candidate):
        return candidate
    if os.path.isdir("templates"):
        return "templates"
    raise FileNotFoundError("Template directory not found: templates")


def load_template_assets(template_name=DEFAULT_TEMPLATE_NAME):
    global category_templates, backgrounds, template_dir
    template_dir = resolve_template_dir(template_name)
    category_templates = open(os.path.join(template_dir, "category templates.html"), "r", encoding="utf-8").read()
    backgrounds = read_backgrounds(template_dir)
    return template_dir


def read_backgrounds(template_dir=None):
    if template_dir is None:
        template_dir = resolve_template_dir(DEFAULT_TEMPLATE_NAME)
    # use regular expression to extract "[begin <background name>]"

    background_file = open(os.path.join(template_dir, "background.css"), "r", encoding="utf-8").read()

    regex = r"\[begin ([a-zA-Z0-9 ]+)\]"
    matches = re.finditer(regex, background_file, re.MULTILINE)
    backgrounds = []
    for matchNum, match in enumerate(matches, start=1):
        background_name = match.group(1)

        stop_tag = "[end " + background_name + "]"
        pos1 = background_file.find(match.group(0)) + len(match.group(0))
        pos2 = background_file.find(stop_tag, pos1)
        if pos2 != -1:
            backgrounds.append(background_file[pos1:pos2])
    return backgrounds


template_dir = resolve_template_dir(DEFAULT_TEMPLATE_NAME)
category_templates = open(os.path.join(template_dir, "category templates.html"), "r", encoding="utf-8").read()
backgrounds = read_backgrounds(template_dir)

def get_background(title):
    sel = int(hashlib.sha1(title.encode("utf-8")).hexdigest(), 16)
    sel = sel % len(backgrounds)
    return backgrounds[sel]


def find_media_type(media):
    if any(x in media["media link"] for x in [".jpg", ".jpeg", ".png", ".svg", ".gif"]): 
        return "image"
    elif any(x in media["media link"] for x in [".mp3"]):
        return "audio"
    else:
        return "video"


def convert_to_html(md_text):
    textpos = 0
    html = ""
    while textpos < len(md_text) - 2:
        if md_text[textpos:textpos+2] == "![":
            # convert markdown until here
            html += markdown.markdown(md_text[0:textpos])
            md_text = md_text[textpos:]
            textpos = 0

            # extract media information
            media = {}
            media["media alt"] = md_text[textpos+2:md_text.find("](", textpos)]
            textpos = md_text.find("](", textpos)
            media["media link"] = md_text[textpos + 2 : md_text.find(")", textpos)]
            media_end = md_text.find(")", textpos) + 1
            media["type"] = find_media_type(media)

            # fix for mastodon gifs
            if "GIF" in media["media alt"]:
                print(media["media alt"])
                media["type"] = "gif"
            media_html = forge_from_template("media " + media["type"], media)["html"]
            html += media_html

            # reset parser
            md_text = md_text[media_end:]
            textpos = 0     
        textpos += 1
    html += markdown.markdown(md_text[0:])
    return html

def convert_to_plaintext(md_text):
    textpos = 0
    text = ""
    while textpos < len(md_text) - 2:

        # handle media
        if md_text[textpos:textpos+2] == "![":
            # convert markdown until here
            text += md_text[0:textpos]
            md_text = md_text[textpos:]
            textpos = 0

            # extract media information
            media = {}
            media["media alt"] = md_text[textpos+2:md_text.find("](", textpos)]
            textpos = md_text.find("](", textpos)
            media["media link"] = md_text[textpos + 2 : md_text.find(")", textpos)]
            media_end = md_text.find(")", textpos) + 1
            media["type"] =  find_media_type(media)           # insert media text   
            media_text = forge_from_template("media " + media["type"], media)["text"]

            text += media_text

            # reset parser
            md_text = md_text[media_end:]
            textpos = 0     
        textpos += 1
    text += md_text[0:]
    return text


def forge_from_template(template_name, content):
    template = get_category_template(template_name)
    return multi_insert_in_category_template(template, content)

def isolate_template(template_name):
    start_tag = "[begin " + template_name + "]"
    end_tag = "[end " + template_name + "]"
    pos1 = category_templates.find(start_tag) + len(start_tag)
    pos2 = category_templates.find(end_tag)
    if pos2 != -1:
        return category_templates[pos1:pos2]
    else:
        return ""


def multi_insert_in_category_template(template, content):
    for key, value in content.items():
        if value: 
            if isinstance(value, str):
                template = insert_in_template(template, key, value)
            elif "html" in value and "text" in value:
                template = insert_in_template(template, key, value)
            elif key == "media":
                template = insert_media_in_template(template, value)
            else:
                template = multi_insert_in_category_template(template, value)
    return template

def get_category_template(template_name):
    html = isolate_template(template_name + " html")
    if not html:
        print("Warning: No HTML template specified for " + template_name)
    text = isolate_template(template_name + " text")
    if not text:
        print("Warning: No text template specified for " + template_name)
    return {"html": html, "text": text}


def insert_in_template(template, key, value):
    if isinstance(value, str):
        template["html"] = template["html"].replace("[insert " + key + "]", value)
        template["text"] = template["text"].replace("[insert " + key + "]", value) 
    else:
        template["html"] = template["html"].replace("[insert " + key + "]", value["html"])
        template["text"] = template["text"].replace("[insert " + key + "]", value["text"]) 
    return template

def insert_media_in_template(template, media):
    """
    
    """
    media_template = ""
    if "video" in media["type"]:
        media_template = forge_from_template("media video", media)
    elif "image" in media["type"]:
        media_template = forge_from_template("media image", media)
    elif "gif" in media["type"]:
        media_template = forge_from_template("media gif", media)
   
    return insert_in_template(template, "media", media_template)
    
def compare_articles(article):
    return int(article["month_num"]) * 100 + int(article["date"])

def fetch_articles():
    body = bridges.local.fetch_content()
    bridges.mastodon.write_articles(body["start"], body["end"])


def tag_html_block(html, article_id):
    if not html:
        return html
    return re.sub(
        r"(<(?:div|section|article)\b)",
        rf'\1 data-article-id="{article_id}"',
        html,
        count=1,
        flags=re.IGNORECASE,
    )


def generate_body(local_linking=False, template_name=DEFAULT_TEMPLATE_NAME, write_files=True):
    """
    Generates the newsletter body from the content fetched from the bridges
    
    :param local_linking: bool
    :param template_name: str
    :param write_files: bool
    """

    template_dir = load_template_assets(template_name)
    body = bridges.local.fetch_content(local_linking)

    # fetch articles from mastodon
    # body["articles"] = bridges.mastodon.fetch_articles(body["start"], body["end"])

    """
    try: 
        month_num = (int(body["number"]) + 2) % 12 + 1
        body["articles"] = body["articles"] + bridges.mastodon.fetch_articles(month_num)
    except:
        print("Konnte Ausgabennummer nicht mit Monat verknüpfen")  
    """   

    body["articles"].sort(key=compare_articles)

    template_html = open(os.path.join(template_dir, "template.html"), "r", encoding="utf-8").read()
    template_html = template_html.replace("[insert iso-timestamp]", datetime.datetime.now().astimezone().isoformat())
    if "start" in body:
        template_html = template_html.replace("[insert newsletter-starts]", body["start"].astimezone().isoformat())
        template_html = template_html.replace("[insert newsletter-ends]", body["end"].astimezone().isoformat())

    template_text = open(os.path.join(template_dir, "template.txt"), "r", encoding="utf-8").read()
    template = {"html": template_html, "text": template_text}

    template = insert_in_template(template, "newsletter title", body["title"])
    template = insert_in_template(template, "newsletter number", body["number"])
    template = insert_in_template(template, "background", get_background(body["title"]))
    
    intro = multi_insert_in_category_template(get_category_template("introduction"), body["intro"])
    intro["html"] = tag_html_block(intro["html"], "intro")
    template = insert_in_template(template, "introduction", intro)

    current_month = "Keinvember"
    articles_html = ""
    articles_text = ""
    for article in body["articles"]:
        if article["month"] != current_month:
            current_month = article["month"]
            divider = forge_from_template("chapter", article)
            articles_html += divider["html"]
            articles_text += divider["text"] 
        tmp = multi_insert_in_category_template(get_category_template(article["class"]), article)
        source_id = article.get("source_index")
        if source_id is not None:
            tmp["html"] = tag_html_block(tmp["html"], f"src-{source_id}")
        articles_html += tmp["html"]
        articles_text += tmp["text"]
    articles = {"html": articles_html, "text": articles_text}

    template = insert_in_template(template, "articles", articles)
    #pp.pprint(body)

    # do important username replacement
    for username, replacename in usernames.items():
        searchname = username.replace("@", "@<span>")
        searchname += "</span>"
        template["html"] = template["html"].replace(searchname, replacename)
        template["text"] = template["text"].replace(searchname, replacename)

    html = template["html"].replace("<br />", "<br>")
    text = template["text"]

    if write_files:
        news_html = open("content/newsletter.html", "w")
        news_html.write(html)
        print("HTML Datei geschrieben.")

        news_text = open("content/newsletter.txt", "w")
        news_text.write(text)
        print("Textdatei geschrieben.")

        news_html.close()
        news_text.close()

    return {"html": html, "text": text}
    

def get_title(use_english=False):
    news_filename = "newsletter"
    if use_english:
        news_filename = "en"
    with open("content/" + news_filename + ".html", "r") as html:
        soup = BeautifulSoup(html.read(), 'html.parser') 
        text = soup.find('h1').find_all("div")
        try: 
            text = text[2].text.strip()[2:-2] + " - " + text[0].text.strip() + " " + text[1].text.strip()
        except:
            text = text.text
            print("Titel enthält nicht-standardisierte Informationen.")
        return text.replace("<br>", "")