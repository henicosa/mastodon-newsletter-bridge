import feedparser

import body
import pprint
import markdown
import time


pp = pprint.PrettyPrinter(indent=2, width=530, compact=True)
months = ["Januar", "Februar", "März", "April", "Mai", "Juni", "Juli", "August", "September", "Oktober", "November", "Dezember"]


def fetch_articles():
    articles = []
    NewsFeed = feedparser.parse("https://social.bau-ha.us/@viji5369.rss")
           
    for entry in NewsFeed.entries:
        entry["published_parsed"] = time.gmtime(time.mktime(entry["published_parsed"]) - time.mktime(time.gmtime(60*60*6)))
        if entry["published_parsed"].tm_mon == 10:
            article = {}
            article["date"] = str(entry["published_parsed"].tm_mday)
            article["month_num"] = str(entry["published_parsed"].tm_mon)
            article["month"] = months[int(article["month_num"]) - 1][0:3]
            article["full_month"] = months[int(article["month_num"]) - 1]
            article["class"] = "article"
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

    return articles