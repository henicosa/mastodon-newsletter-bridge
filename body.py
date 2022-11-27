import bridges.local
import bridges.mastodon
import markdown
import pprint

pp = pprint.PrettyPrinter(indent=2, width=530, compact=True)

category_templates = open("templates/category templates.html", "r").read()

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
            media["type"] = "video"
            if any(x in media["media link"] for x in [".jpg", ".jpeg", ".png", ".svg", ".gif"]): 
                media["type"] = "image"
            
            # insert media html   
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
            media["type"] = "video"
            if any(x in media["media link"] for x in [".jpg", ".jpeg", ".png", ".svg", ".gif"]): 
                media["type"] = "image"
            
            # insert media text   
            media_text = forge_from_template("media " + media["type"], media)["text"]
            text += text

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
    
def generate_body():
    body = bridges.local.fetch_content()
    body["articles"] = body["articles"] + bridges.mastodon.fetch_articles()    
    body["articles"].sort(key=compare_articles)

    template_html = open("templates/template.html", "r").read()
    template_text = open("templates/template.txt", "r").read()
    template = {"html": template_html, "text": template_text}

    template = insert_in_template(template, "newsletter title", body["title"])
    template = insert_in_template(template, "newsletter number", body["number"])
    
    intro = multi_insert_in_category_template(get_category_template("introduction"), body["intro"])
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
        articles_html += tmp["html"]
        articles_text += tmp["text"]
    articles = {"html": articles_html, "text": articles_text}

    template = insert_in_template(template, "articles", articles)


    #pp.pprint(body)

    # store newsletter in content directory
    news_html = open("content/newsletter.html", "w")
    news_html.write(template["html"].replace("<br />", "<br>"))

    news_text = open("content/newsletter.txt", "w")
    news_text.write(template["text"])

    news_html.close()
    news_text.close()
    