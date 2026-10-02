# Mastodon Newsletter Bridge

This project generates a monthly email newsletter from a Markdown editorial file and optional Mastodon posts, then sends it to the configured subscriber list.

The main workflow is coordinated in `main.py`:

- `generate` composes the newsletter body from the source content
- `publish` generates the HTML/text version and sends it to subscribers
- `debug` sends the current newsletter to a configured debug address
- `fetch_articles` imports recent Mastodon posts into the source content

---

## Project structure

- `main.py`: CLI entry point and orchestration
- `app.py`: local Flask editor with live newsletter preview
- `body.py`: content parsing, article conversion, template insertion, newsletter generation
- `mail.py`: email sending and subscriber management
- `bridges/local.py`: parses the local editorial content from `content/content.md`
- `bridges/mastodon.py`: fetches Mastodon posts and writes them into the content file
- `content/`: generated newsletter output and editorial source files
- `templates/`: HTML/text templates and category templates
- `web/`: editor page, styles, and client script
- `secrets/`: mail credentials and subscriber recipient lists
- `archive/`: timestamped copies of newsletter content after publishing

---

## Required setup

1. Create the `secrets/secrets.json` file.
2. Fill in the SMTP sender details, debug recipient, and any other required keys.
3. Create the subscriber lists in `secrets/subscribers.txt` and `secrets/subscribers_en.txt`.
4. Prepare the editorial source in `content/content.md`.
5. Install dependencies from `requirements.txt`.

Example structure for `secrets/secrets.json`:

```json
{
  "sender": {
    "email": "newsletter@example.com",
    "password": "...",
    "server-domain": "mail.example.com",
    "server-port": "465"
  },
  "debug-receiver": {
    "email": "debug@example.com",
    "name": "Debug Receiver"
  }
}
```

Subscriber files use a simple format:

```text
first.last@example.com Full Name
second@example.com Another Person
```

Lines starting with `#` are ignored.

---

## Source content format

The newsletter content is largely driven by `content/content.md`.

This file contains:

- Frontmatter with the mailing period (`start` and `end` dates)
- A title and issue number
- Introductory text
- One or more article sections, each written as a block beginning with a date and article class

A typical local article entry looks like this:

```md
12.05 article
This is the article body.

### source
Example source text.
```

The parser in `bridges/local.py` reads these blocks, extracts the date and class, then converts the article text into HTML and plain text for the newsletter template.

The Mastodon bridge can append posts from a Mastodon account based on the same date range.

---

## Generation flow

The intended workflow starts by fetching recent Mastodon posts into the local content file, then the editor adds manual copy and structure before the final compile step.

```bash
python main.py -f
```

This first imports the newest available Mastodon content into `content/content.md`. After that, the user adds any extra editorial text, introductions, commentary, or custom markdown sections in the same file.

Only after the content has been reviewed and extended should the final newsletter be generated:

```bash
python main.py
```

This calls `generate()` in `main.py`, which triggers:

1. `body.generate_body(local_linking)`
2. `bridges.local.fetch_content(local_linking)` reads the edited `content/content.md`
3. The content is converted into a newsletter structure with title, issue number, intro, and article sections
4. Templates from `templates/template.html` and `templates/template.txt` are filled with the resolved content
5. The generated output is written to:
   - `content/newsletter.html`
   - `content/newsletter.txt`

The body builder also replaces usernames and inserts template backgrounds, chapter dividers, and article-specific formatting.

If `-l` is given, the generator uses local links instead of remote resource URLs.

Examples:

```bash
python main.py -l
```

This is useful when previewing or editing locally without publishing remote asset links.

---

## Preview editor

To edit `content/content.md` with a live HTML preview:

```bash
python app.py
```

Then open `http://127.0.0.1:5000`. The left pane is the Markdown source; the right pane renders the newsletter through the same pipeline as `python main.py -l`. Typing autosaves `content/content.md` after a short delay. Use the template dropdown to switch themes. Publishing and Mastodon fetch stay in the CLI.

---

## Publishing flow

Publishing is triggered with:

```bash
python main.py -p
```

This sequence happens:

1. `main.py` calls `publish(use_english)`
2. `get_saved_content(use_english)` reads the generated newsletter content from `content/newsletter.txt` and `content/newsletter.html` (or `content/en.html` if `-e` is used)
3. `mail.publish_newsletter(mail_content, use_english)` loads the correct subscriber list from `secrets/`
4. Each subscriber receives an HTML email generated from the newsletter content
5. `archive_newsletter(mail_content)` copies both the generated content and the templates directory into `archive/<newsletter-subject>`

The archive folder name is based on the newsletter title extracted from the generated HTML via `body.get_title()`.

---

## English vs German mode

The CLI supports both languages:

- `-e` selects the English version of the newsletter content
- without `-e`, it uses the default German version

Examples:

```bash
python main.py -p -e
python main.py -d -e
```

For the English publish flow, the script reads `content/en.html` and uses `secrets/subscribers_en.txt`.

---

## Debug sending

To test email delivery without broadcasting to the full list:

```bash
python main.py -d
```

This sends the current newsletter to the configured debug recipient in `secrets/secrets.json` via `mail.debug_newsletter(...)`.

This is useful before a real release to verify the subject, formatting, and sender configuration.

---

## Fetching Mastodon articles

The project can import posts from Mastodon into the content file:

```bash
python main.py -f
```

This calls `body.fetch_articles()`, which:

1. Reads the local content window from `bridges/local.py`
2. Queries Mastodon via `bridges/mastodon.py`
3. Extracts posts in the date range
4. Rewrites the relevant section of `content/content.md`

This is how fresh Mastodon posts are pulled into the next issue.

---

## CLI options summary

```bash
python main.py -h
```

Available flags from `main.py`:

- `--init` or `-i`: create a new `content/content.md` for a chosen date range and immediately fetch matching Mastodon posts into it
- `-d`: debug-send the current newsletter
- `-p`: publish the newsletter to subscribers
- `-f`: fetch Mastodon articles into the content file
- `-l`: generate with local asset links
- `-t` or `--template`: choose the template set to use when compiling the newsletter
- `-e`: use the English newsletter variant

---

## Template selection

The project supports multiple visual layouts by storing each template set in its own folder under `templates/`.

Examples:

```bash
python main.py --template default
python main.py --template neo_full_frame
```

The selected directory determines which `template.html`, `template.txt`, category templates, and background assets are used during generation. This keeps each design isolated and makes it easy to swap layouts without changing the content pipeline.

---

## Initial issue setup with `--init`

The project can scaffold a new issue file automatically:

```bash
python main.py --init
```

This will:

1. ask for a start date and end date
2. create or overwrite `content/content.md` with a minimal issue skeleton
3. populate the timeline with Mastodon posts from that date range immediately

After that, the user can open the file and add extra manual content before running the regular generation step:

```bash
python main.py
```

This is the recommended way to start a new newsletter round: fetch and seed the content automatically, then edit the markdown before compiling.

---

## Typical publishing workflow

A normal release usually follows this order:

1. Fetch article data as the starting point:
   ```bash
   python main.py -f
   ```
2. Open `content/content.md` and add the manual extra content for the issue: introductions, summaries, editorial notes, and any additional sections not coming from Mastodon.
3. Review the markdown and adjust the structure before compiling.
4. Generate the issue locally:
   ```bash
   python main.py
   ```
5. Preview the generated output in `content/newsletter.html` and `content/newsletter.txt`
6. Send a debug test:
   ```bash
   python main.py -d
   ```
7. Publish to the real subscriber list:
   ```bash
   python main.py -p
   ```
8. Confirm the newsletter was archived under `archive/<newsletter-subject>`

This keeps the Mastodon import as the data foundation, while the human editorial step decides what extra content is included before the final newsletter is compiled and sent.

---

## Notes

- The email sender currently sends the HTML version only; the plain-text part is not attached in `mail.py`.
- The archive step copies both the generated content folder and the templates folder for later retrieval.
- This project assumes a separate SMTP account and dedicated subscriber lists for newsletter sending.

This is a lightweight automation script rather than a full CMS, so the actual issue structure and content are still maintained directly in the Markdown source files.
