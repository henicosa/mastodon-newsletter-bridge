import mail

def generate_newsletter():
    text = open("content/newsletter.txt", "r").read()
    html = open("content/newsletter.html", "r").read()
    return {"text": text, "html": html}

def debug():
    mail_content = generate_newsletter()
    mail.debug_newsletter(mail_content)

if __name__=="__main__":
    debug()