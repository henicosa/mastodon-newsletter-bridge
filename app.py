import os
import re

from flask import Flask, jsonify, render_template, request, send_from_directory

import body

ROOT = os.path.dirname(os.path.abspath(__file__))
os.chdir(ROOT)

CONTENT_DIR = os.path.join(ROOT, "content")
CONTENT_MD = os.path.join(CONTENT_DIR, "content.md")
TEMPLATES_DIR = os.path.join(ROOT, "templates")

app = Flask(
    __name__,
    template_folder=os.path.join(ROOT, "web", "templates"),
    static_folder=os.path.join(ROOT, "web", "static"),
)


def list_templates():
    names = []
    if not os.path.isdir(TEMPLATES_DIR):
        return [body.DEFAULT_TEMPLATE_NAME]
    for name in sorted(os.listdir(TEMPLATES_DIR)):
        path = os.path.join(TEMPLATES_DIR, name)
        if os.path.isdir(path) and os.path.isfile(os.path.join(path, "template.html")):
            names.append(name)
    return names or [body.DEFAULT_TEMPLATE_NAME]


def prepare_preview_html(html, base_url):
    if re.search(r"<head\b", html, flags=re.IGNORECASE):
        return re.sub(
            r"<head\b[^>]*>",
            lambda match: match.group(0) + f'<base href="{base_url}">',
            html,
            count=1,
            flags=re.IGNORECASE,
        )
    return f'<head><base href="{base_url}"></head>' + html


@app.route("/")
def index():
    return render_template("editor.html", templates=list_templates())


@app.route("/api/content")
def get_content():
    if not os.path.exists(CONTENT_MD):
        return jsonify({"markdown": ""})
    with open(CONTENT_MD, "r", encoding="utf-8") as handle:
        return jsonify({"markdown": handle.read()})


@app.route("/api/preview", methods=["POST"])
def preview():
    data = request.get_json(silent=True) or {}
    markdown_text = data.get("markdown", "")
    template_name = data.get("template") or body.DEFAULT_TEMPLATE_NAME
    if template_name not in list_templates():
        template_name = body.DEFAULT_TEMPLATE_NAME

    os.makedirs(CONTENT_DIR, exist_ok=True)
    with open(CONTENT_MD, "w", encoding="utf-8") as handle:
        handle.write(markdown_text)

    try:
        result = body.generate_body(
            local_linking=True,
            template_name=template_name,
            write_files=False,
        )
        base_url = request.url_root.rstrip("/") + "/content/"
        return jsonify({"html": prepare_preview_html(result["html"], base_url)})
    except Exception as exc:
        return jsonify({"error": str(exc)}), 400


@app.route("/content/<path:filename>")
def content_files(filename):
    return send_from_directory(CONTENT_DIR, filename)


if __name__ == "__main__":
    # Werkzeug's debugger and reloader use multiprocessing primitives that
    # raise BrokenPipeError on Python 3.14 in this environment.
    app.run(debug=False)
