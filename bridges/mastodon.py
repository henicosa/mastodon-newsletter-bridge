#import feedparser

import body
import json
import pprint
import markdown
import time
import datetime
import requests

categories = json.load(open('templates/categories.json', 'r'))

pp = pprint.PrettyPrinter(indent=2, width=530, compact=True)
months = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]

def extract_posts_between_dates(start_date, end_date, max_iterations=30):
    json_url = "https://social.bau-ha.us/api/v1/accounts/192533/statuses?exclude_replies=true&exclude_reblogs=true&limit=40"
    
    all_posts = []
    max_id = None
    iterations = 0

    print("Suche auf mastodon nach Artikel von " + start_date.strftime("%d.%m.%Y") + " bis " + end_date.strftime("%d.%m.%Y"))
    
    while iterations < max_iterations:
        url = json_url
        if max_id:
            url += f"&max_id={max_id}"
        
        response = requests.get(url)
        if response.status_code == 200:
            posts = response.json()
            if not posts:
                break  # No more posts available

            for post in posts:
                created_at = datetime.datetime.fromisoformat(post['created_at'][:-1])  # Convert ISO format to datetime
                if start_date <= created_at <= end_date:
                    all_posts.append(post)
                max_id = int(post['id']) - 1  # Update max_id for next iteration

            if datetime.datetime.fromisoformat(posts[-1]['created_at'][:-1]) < start_date:
                break  # No more posts in time range available

        else:
            print(f"Error: Failed to fetch data (Status code: {response.status_code})")
            break
        
        iterations += 1

    print("Habe", str(len(all_posts)), "Artikel gefunden")

    return all_posts


def convert_toot_to_markdown(toot):
    """
    Converts a toot to markdown
    """
    date_in_d_m_format = datetime.datetime.strptime(toot["created_at"], "%Y-%m-%dT%H:%M:%S.%fZ").strftime("%d.%m")
    article_class = "article-mastodon"
    if "tags" in toot:
        for tag in toot["tags"]:
            print("tag", tag["name"])
            for category in categories:
                if tag["name"] in categories[category]:
                    print("category", category)
                    article_class = category
                    break

    md = "## " + date_in_d_m_format  + " " + article_class + "\n"
    
    md_media = "\n## media_attachments\n"
    
    if toot["media_attachments"]:
        for media in toot["media_attachments"]:
            md += "![" + str(media["description"]) + "](" + media["preview_url"] + ")\n"
            md_media += "### media\n#### media link\n" + media["preview_url"] + "#### media alt\n" + str(media["description"]) + "\n"

    md += toot["content"] + "\n"

    if toot["card"]:
        md += "\n### card\n![" + str(toot["card"]["title"]) + "](" + str(toot["card"]["image"]) + ")\n"

    


    #if md_media != "\n## media\n":
    #    md += md_media

    md += "\n\n"
    return md


def write_articles(start, end):
    """
    Writes articles to a markdown file
    
    :param start: datetime.datetime
    :param end: datetime.datetime
    """
    posts = extract_posts_between_dates(start, end)
    md = ""
    for post in posts:
        md += convert_toot_to_markdown(post)
    content_md = open("content/content.md", "r").read()
    if "# Mastodon" in content_md:
        # only replace mastodon section
        section_start = content_md.find("\n# Mastodon")
        section_end = content_md.find("\n# ", section_start + 1)
        content_md = content_md[:section_start] + "\n# Mastodon\n" + md + content_md[section_end:]
    else:
        content_md += "\n# Mastodon\n" + md
    open("content/content.md", "w").write(content_md)


def fetch_articles(start, end):
    """
    Fetches articles from mastodon
    
    :param start: datetime.datetime
    :param end: datetime.datetime
    :return: list of articles
    """

    print("Suche auf mastodon nach Artikel von" + str(start) + " bis " + str(end) )
    articles = []
    posts = extract_posts_between_dates(start, end)
           
    for entry in posts:

        entry["created_at"] = datetime.datetime.fromisoformat(entry["created_at"][:-1])  # Convert ISO format to datetime
        entry_is_inbetween = start <= entry["created_at"] <= end
        if entry_is_inbetween:
            article = {}
            article["date"] = str(entry["created_at"].day)
            article["month_num"] = str(entry["created_at"].month)
            months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"]
            article["month"] = months[int(article["month_num"]) - 1][0:3]
            article["full_month"] = months[int(article["month_num"]) - 1]
            article["origin"] = "article-mastodon"
            article["class"] = "article-mastodon"
            article["source"] = {"html": f"<a href=\"{entry['url']}\">@{entry['account']['username']}@social.bau-ha.us</a>","text": f"mastodon: @{entry['account']['username']}@bau-ha.us"}
            article["media"] = {"type": "no media"}

            if entry["media_attachments"]:
                article["origin"] = "article-mastodon"
                media_attachment = entry["media_attachments"][0]
                article["media"] = {"media link": media_attachment["url"], "media alt": media_attachment["description"]}
                article["media"]["type"] = media_attachment["type"]
                if "video" in article["media"]["type"]:
                    article["media"]["type"] = "gif"
            
            article["root"] = {"html": entry["content"], "text": ""}  # Assuming "content" contains HTML
            articles.append(article)

        """
        entry["published_parsed"] = time.gmtime(time.mktime(entry["published_parsed"]) - time.mktime(time.gmtime(60*60*6)))
        entry_datetime = datetime.datetime.fromtimestamp(time.mktime(entry["published_parsed"]))
        entry_is_inbetween = start <= entry_datetime <= end
        if entry_is_inbetween:
            article = {}
            article["date"] = str(entry["published_parsed"].tm_mday)
            article["month_num"] = str(entry["published_parsed"].tm_mon)
            article["month"] = months[int(article["month_num"]) - 1][0:3]
            article["full_month"] = months[int(article["month_num"]) - 1]
            article["class"] = "article-mastodon"
            article["source"] = {"html": "<a href=\"https://social.bau-ha.us/@viji5369\">@viji5369@social.bau-ha.us</a>","text": "mastodon: @viji5369@bau-ha.us"}
            article["media"] = {"type": "no media"}

            if "media_content" in entry:
                if "content" in entry:
                    article["media"] = {"media link": entry["media_content"][0]["url"], "media alt": entry["content"][0]["value"]}
                else:
                    article["media"] = {"media link": entry["media_content"][0]["url"], "media alt": "Keine Bildbeschreibung verfügbar."}
                article["media"]["type"] = entry["media_content"][0]["type"] 
                if "video" in article["media"]["type"]:
                    article["media"]["type"] = "gif"
            root = entry["summary"]
            article["root"] = {"html": body.convert_to_html(root), "text": body.convert_to_plaintext(root)}
            articles.append(article)
        """

    print("Habe", str(len(articles)), "Artikel gefunden")

    pprint.pprint(articles)

    return articles