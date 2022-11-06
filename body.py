import bridges.local
import pprint

pp = pprint.PrettyPrinter(indent=2, width=530, compact=True)

category_templates = open("templates/category templates.html", "r").read()

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

def fetch_mastodon_articles():
    return []

def compare_articles(article):
    return int(article["month_num"]) * 100 + int(article["date"])
    
def generate_body():
    body = bridges.local.fetch_content()
    body["articles"] = body["articles"] + fetch_mastodon_articles()    
    body["articles"].sort(key=compare_articles)

    template_html = open("templates/template.html", "r").read()
    template_text = open("templates/template.txt", "r").read()
    template = {"html": template_html, "text": template_text}

    template = insert_in_template(template, "newsletter title", body["title"])
    template = insert_in_template(template, "newsletter number", body["number"])
    
    intro = multi_insert_in_category_template(get_category_template("introduction"), body["intro"])
    template = insert_in_template(template, "introduction", intro)

    articles_html = ""
    articles_text = ""
    for article in body["articles"]:
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
    