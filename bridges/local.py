import markdown
import body
import sys

months = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

def fit_text(text):
    while text and text[0] == "\n" or text[0] == " ":
        text = text[1:]
    while text and text[-1] == "\n" or text[-1] == " ":
        text = text[:-1]
    return text
    
def parse_media(root, article_class):
    media = {"type": "no media"}
    if root.startswith("!["):
        media = {}
        media["media alt"] = root[2:root.find("]")]
        media["media link"] = root[root.find("](") + 2 : root.find(")", root.find("]("))]
        media["type"] = "image"
        if article_class != "article" and article_class != "article-mastodon":
            root = root[root.find("\n", root.find(")", root.find("](")))+1:]
        root = fit_text(root)
    return [root, media]
    

def fetch_local_article(raw_article):
    article = {}
    next_line_index = raw_article.find("\n")
    first_line = raw_article[:next_line_index]
    first_line = first_line.split(" ")
    article["date"] = first_line[0].split(".")[0]
    article["month_num"] = first_line[0].split(".")[1]
    article["month"] = months[int(article["month_num"]) - 1][0:3]
    article["full_month"] = months[int(article["month_num"]) - 1]
    article["class"] = "".join(first_line[1:])
    article["source"] = "Exklusiver Inhalt"
    article["media"] = []
    if not article["class"]:
        article["class"] = "article"

    raw_article = raw_article[(next_line_index+1):]
    article_items = raw_article.split("### ")

    root = fit_text(article_items.pop(0))

    [root, media] = parse_media(root, article["class"])
    


    # parse media

    if media:
        article["media"] = media

    article["root"] = {"html": body.convert_to_html(root), "text": body.convert_to_plaintext(root)}
    
    # process other items
    for item in article_items:
        item = fit_text(item)
        item = item.split("\n")
        key = item[0]
        value = "".join(item[1:])
        article[key] = value

    return article

from datetime import datetime
from dateutil import parser

def parse_frontmatter(content):
    frontmatter_lines = []
    content_lines = content.splitlines()
    
    # Find the start and end of frontmatter
    start_index, end_index = None, None
    for i, line in enumerate(content_lines):
        if line.strip() == '---':
            if start_index is None:
                start_index = i
            elif end_index is None:
                end_index = i
                break
    
    if start_index is not None and end_index is not None:
        frontmatter_lines = content_lines[start_index+1:end_index]
    
    frontmatter_data = {}
    for line in frontmatter_lines:
        key_value = line.split(':', 1)
        if len(key_value) == 2:
            key = key_value[0].strip()
            value = key_value[1].strip()
            frontmatter_data[key] = value
    
    return frontmatter_data


def extract_dates_from_markdown(content):
    post = parse_frontmatter(content)
    
    if 'start' in post.keys() and 'end' in post.keys():
        start_date = parser.parse(post['start'])
        end_date = parser.parse(post['end'])
        return start_date, end_date
    else:
        return None, None

def fetch_content(local_linking=False):
    news = {}

    content_level = open("content/content.md", "r").read()
    
    news["start"], news["end"] = extract_dates_from_markdown(content_level)
    
    content_level = "".join(content_level.split("---\n")[2:])

    # replace local url with server urls
    server_base_url = "https://ludattel.de/newsletter/resources"
    if not local_linking:
        content_level = content_level.replace("](resources", "](" + server_base_url)

    h1_level = content_level.split("\n# ")
    
    # parse headline
    headlines = h1_level[0].split("\n")
    news["title"] = headlines[0].replace("# ", "")
    news["number"] = headlines[1].replace("## ", "")

    # parse intro

    intro = {}
    intro_raw = h1_level[1]
    intro_raw = intro_raw[intro_raw.find("\n")+1:]
    [intro_raw, media] = parse_media(intro_raw, "intro")
    root = intro_raw
    if media:
        intro["media link"] = media["media link"]
        intro["media alt"] = media["media alt"]
    intro["root"] = {"html": markdown.markdown(root), "text": root}
    news["intro"] = intro
    

    # parse timeline
    articles = []
    articles_raw = h1_level[2].split("\n## ")
    for raw_article in articles_raw[1:]:
        articles.append(fetch_local_article(raw_article))
    news["articles"] = articles
    return news