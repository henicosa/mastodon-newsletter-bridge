# importing the requests library
import requests
import json
from bs4 import BeautifulSoup

def read_secrets():
    return json.load(open('secrets/secrets.json', 'r'))

secrets = read_secrets()

def translate_to_english(text):
    result = requests.get( 
    "https://api-free.deepl.com/v2/translate", 
    params={ 
        "auth_key": secrets["translator"]["deepl-api-key"], 
        "target_lang": "en", 
        "text": text, 
        "tag_handling": "html",
    }, 
    ) 
    #print(result.json())
    return result.json()["translations"][0]["text"]

def translate_newsletter_html_to_english():
    html_doc = open("content/newsletter.html", "r").read()

    soup = BeautifulSoup(html_doc, 'html.parser')

    tags_to_translate = ["p", "title"]

    for html_tag in tags_to_translate:
        instances = soup.find_all(html_tag)
        instances_length = str(len(instances))
        print("Processing " + html_tag + " with " + instances_length + " instances.")
        for instance in instances:
            newtag = BeautifulSoup(translate_to_english(str(instance)), "html.parser")
            instance.replace_with(newtag)

    classes_to_translate = ["chapter-start-title", "timeline-author", "translatable"]

    for html_class in classes_to_translate:
        instances = soup.find_all(class_=html_class)
        instances_length = str(len(instances))
        print("Processing " + html_class + " with " + instances_length + " instances.")
        for instance in instances:
            newtag = BeautifulSoup(translate_to_english(str(instance)), "html.parser")
            instance.replace_with(newtag)

    html_en = open("content/en.html", "w")
    html_en.write(soup.prettify().replace("_deutsch", "_english"))

translate_newsletter_html_to_english()