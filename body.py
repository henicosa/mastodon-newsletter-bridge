import markdown

def fit_text(text):
    while text and text[0] == "\n" or text[0] == " ":
        text = text[1:]
    while text and text[-1] == "\n" or text[-1] == " ":
        text = text[:-1]
    return text
    

def fetch_local_article(raw_article):
    article = {}
    next_line_index = raw_article.find("\n")
    first_line = raw_article[:next_line_index]
    first_line = first_line.split(" ")
    article["date"] = first_line[0].split(".")[0]
    article["month"] = first_line[0].split(".")[1]
    article["class"] = "".join(first_line[1:])
    if not article["class"]:
        article["class"] = "plain"
    
    raw_article = raw_article[(next_line_index+1):]
    article_items = raw_article.split("### ")
    root = fit_text(article_items.pop(0))

    # parse image
    if root.startswith("!["):
        image = {}
        image["alt"] = root[2:root.find("]")]
        image["source"] = root[root.find("](") + 2 : root.find(")", root.find("]("))]
        article["media"] = [image]
        root = root[root.find("\n", root.find(")", root.find("](")))+1:]
        root = fit_text(root)
    article["root"] = {"html": markdown.markdown(root), "text": root}

    # process other items
    for item in article_items:
        item = fit_text(item)
        item = item.split("\n")
        key = item[0]
        value = "".join(item[1:])
        article[key] = value

    return article

def fetch_local_content():
    news = {}

    content_level = open("content/content.md", "r").read()
    h1_level = content_level.split("\n# ")
    
    # parse headline
    headlines = h1_level[0].split("\n")
    news["title"] = headlines[0].replace("# ", "")
    news["number"] = headlines[1].replace("## ", "")

    # parse intro
    intro = {}
    intro_raw = h1_level[1]

    # parse timeline
    articles = []
    articles_raw = h1_level[2].split("\n## ")
    for raw_article in articles_raw[1:]:
        articles.append(fetch_local_article(raw_article))
