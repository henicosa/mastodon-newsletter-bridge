const editorPane = document.getElementById("editor-pane");
const editorList = document.getElementById("editor-list");
const templateSelect = document.getElementById("template-select");
const previewFrame = document.getElementById("preview-frame");
const previewError = document.getElementById("preview-error");
const statusEl = document.getElementById("status");

const PREVIEW_DELAY_MS = 400;
const ARTICLE_TYPES = [
  "article",
  "article-mastodon",
  "article-mastodon-cw",
  "traveltipps",
  "typo",
  "feinedinge",
  "arthur",
  "sprachlabor",
  "redaktion",
  "map",
  "video",
];

let previewTimer = null;
let requestId = 0;
let preamble = "";
let articles = [];
let activeId = "intro";
let ignoreScrollSync = false;

function setStatus(message, isError = false) {
  statusEl.textContent = message;
  statusEl.classList.toggle("is-error", isError);
}

function formatTime(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

function parseHeading(line) {
  const parts = line.replace(/^##\s*/, "").trim().split(/\s+/).filter(Boolean);
  return {
    date: parts[0] || "01.01",
    klass: parts.slice(1).join(" ") || "article",
  };
}

function dateSortKey(dateStr) {
  const parts = String(dateStr || "").trim().split(".");
  const day = parseInt(parts[0], 10);
  const month = parseInt(parts[1], 10);
  if (Number.isNaN(day) || Number.isNaN(month)) {
    return Number.MAX_SAFE_INTEGER;
  }
  return month * 100 + day;
}

function sortedArticles() {
  return [...articles].sort((left, right) => {
    const diff = dateSortKey(left.date) - dateSortKey(right.date);
    return diff !== 0 ? diff : left.sourceIndex - right.sourceIndex;
  });
}

function splitMarkdown(markdown) {
  const match = /^# Timeline[ \t]*$/m.exec(markdown);
  if (!match) {
    return { preamble: markdown, articles: [] };
  }
  const lineEnd = markdown.indexOf("\n", match.index);
  const preambleEnd = lineEnd === -1 ? markdown.length : lineEnd + 1;
  const nextPreamble = markdown.slice(0, preambleEnd);
  const rest = markdown.slice(preambleEnd);
  const starts = [];
  const headingRe = /^## /gm;
  let headingMatch;
  while ((headingMatch = headingRe.exec(rest)) !== null) {
    starts.push(headingMatch.index);
  }
  const nextArticles = starts.map((start, index) => {
    const end = index + 1 < starts.length ? starts[index + 1] : rest.length;
    const raw = rest.slice(start, end);
    const newline = raw.indexOf("\n");
    const heading = newline === -1 ? raw : raw.slice(0, newline);
    const parsed = parseHeading(heading);
    return {
      id: `src-${index}`,
      sourceIndex: index,
      date: parsed.date,
      klass: parsed.klass,
      body: newline === -1 ? "" : raw.slice(newline + 1),
    };
  });
  return { preamble: nextPreamble, articles: nextArticles };
}

function serializeArticle(article) {
  const date = (article.date || "01.01").trim();
  const klass = (article.klass || "article").trim();
  return `## ${date} ${klass}\n${article.body}`;
}

function joinMarkdown() {
  return preamble + articles.map(serializeArticle).join("");
}

function extractImages(text) {
  const urls = [];
  const markdownRe = /!\[[^\]]*\]\(([^)\s]+)\)/g;
  const htmlRe = /<img[^>]+src=["']([^"']+)["']/gi;
  let match;
  while ((match = markdownRe.exec(text)) !== null) {
    if (match[1] && match[1] !== "None") {
      urls.push(match[1]);
    }
  }
  while ((match = htmlRe.exec(text)) !== null) {
    if (match[1] && match[1] !== "None") {
      urls.push(match[1]);
    }
  }
  return [...new Set(urls)];
}

function resolveImageUrl(url) {
  if (/^https?:\/\//i.test(url) || url.startsWith("/")) {
    return url;
  }
  return "/content/" + url.replace(/^\.\//, "");
}

function autosize(textarea) {
  textarea.style.height = "auto";
  textarea.style.height = `${textarea.scrollHeight}px`;
}

function setActiveCard(id) {
  activeId = id;
  for (const block of editorList.querySelectorAll(".article-block")) {
    block.classList.toggle("is-active", block.dataset.articleId === id);
  }
}

function scrollPreviewTo(id) {
  const doc = previewFrame.contentDocument;
  if (!doc) {
    return;
  }
  const target = doc.querySelector(`[data-article-id="${id}"]`);
  if (!target) {
    if (id === "intro") {
      doc.documentElement.scrollTo({ top: 0, behavior: "smooth" });
    }
    return;
  }
  target.scrollIntoView({ behavior: "smooth", block: "start" });
}

function updateActiveFromScroll() {
  if (ignoreScrollSync) {
    return;
  }
  const blocks = [...editorList.querySelectorAll(".article-block")];
  if (!blocks.length) {
    return;
  }
  const marker = editorPane.getBoundingClientRect().top + 48;
  let next = blocks[0];
  for (const block of blocks) {
    if (block.getBoundingClientRect().top <= marker) {
      next = block;
    } else {
      break;
    }
  }
  if (next.dataset.articleId !== activeId) {
    setActiveCard(next.dataset.articleId);
    scrollPreviewTo(activeId);
  }
}

function showPreview(html) {
  previewError.hidden = true;
  previewFrame.hidden = false;
  previewFrame.srcdoc = html;
}

function showError(message) {
  previewFrame.hidden = true;
  previewError.hidden = false;
  previewError.textContent = message;
}

function createImagePreview(text) {
  const urls = extractImages(text);
  const row = document.createElement("div");
  row.className = "image-preview";
  if (!urls.length) {
    row.hidden = true;
    return row;
  }
  for (const url of urls) {
    const image = document.createElement("img");
    image.src = resolveImageUrl(url);
    image.alt = "";
    image.addEventListener("error", () => {
      image.remove();
      if (!row.querySelector("img")) {
        row.hidden = true;
      }
    });
    row.append(image);
  }
  return row;
}

function refreshImagePreview(row, text) {
  const next = createImagePreview(text);
  row.replaceWith(next);
  return next;
}

function fillTypeSelect(select, current) {
  const types = ARTICLE_TYPES.includes(current) ? ARTICLE_TYPES : [current, ...ARTICLE_TYPES];
  for (const type of types) {
    const option = document.createElement("option");
    option.value = type;
    option.textContent = type;
    if (type === current) {
      option.selected = true;
    }
    select.append(option);
  }
}

function activateFrom(id) {
  setActiveCard(id);
  scrollPreviewTo(id);
}

function createIntroBlock() {
  const block = document.createElement("div");
  block.className = "article-block";
  block.dataset.articleId = "intro";

  const over = document.createElement("div");
  over.className = "article-over";
  const label = document.createElement("span");
  label.className = "article-over-label";
  label.textContent = "Intro";
  over.append(label);

  const card = document.createElement("article");
  card.className = "article-card";

  let preview = createImagePreview(preamble);
  const textarea = document.createElement("textarea");
  textarea.spellcheck = false;
  textarea.value = preamble;
  textarea.setAttribute("aria-label", "Intro");

  textarea.addEventListener("focus", () => activateFrom("intro"));
  textarea.addEventListener("input", () => {
    preamble = textarea.value;
    preview = refreshImagePreview(preview, preamble);
    card.prepend(preview);
    autosize(textarea);
    schedulePreview();
  });

  card.append(preview, textarea);
  block.append(over, card);
  return block;
}

function createArticleBlock(article) {
  const block = document.createElement("div");
  block.className = "article-block";
  block.dataset.articleId = article.id;

  const over = document.createElement("div");
  over.className = "article-over";

  const dateInput = document.createElement("input");
  dateInput.type = "text";
  dateInput.className = "article-date-input";
  dateInput.value = article.date;
  dateInput.placeholder = "TT.MM";
  dateInput.setAttribute("aria-label", "Datum");

  const typeSelect = document.createElement("select");
  typeSelect.className = "article-type-select";
  typeSelect.setAttribute("aria-label", "Artikeltyp");
  fillTypeSelect(typeSelect, article.klass);

  const remove = document.createElement("button");
  remove.type = "button";
  remove.className = "delete-button";
  remove.textContent = "Löschen";
  remove.addEventListener("click", () => {
    if (!window.confirm("Diesen Artikel wirklich löschen?")) {
      return;
    }
    articles = articles.filter((item) => item.id !== article.id);
    articles.forEach((item, index) => {
      item.sourceIndex = index;
      item.id = `src-${index}`;
    });
    if (activeId === article.id) {
      activeId = "intro";
    }
    renderCards();
    previewNow();
  });

  over.append(dateInput, typeSelect, remove);

  const card = document.createElement("article");
  card.className = "article-card";

  let preview = createImagePreview(article.body);
  const textarea = document.createElement("textarea");
  textarea.spellcheck = false;
  textarea.value = article.body;
  textarea.setAttribute("aria-label", `Artikel ${article.date}`);

  dateInput.addEventListener("focus", () => activateFrom(article.id));
  typeSelect.addEventListener("focus", () => activateFrom(article.id));
  textarea.addEventListener("focus", () => activateFrom(article.id));

  dateInput.addEventListener("input", () => {
    article.date = dateInput.value;
    schedulePreview();
  });
  dateInput.addEventListener("change", () => {
    article.date = dateInput.value;
    renderCards();
    previewNow();
    const nextDate = editorList.querySelector(
      `.article-block[data-article-id="${article.id}"] .article-date-input`,
    );
    if (nextDate) {
      nextDate.focus();
    }
  });

  typeSelect.addEventListener("change", () => {
    article.klass = typeSelect.value;
    previewNow();
  });

  textarea.addEventListener("input", () => {
    article.body = textarea.value;
    preview = refreshImagePreview(preview, article.body);
    card.prepend(preview);
    autosize(textarea);
    schedulePreview();
  });

  card.append(preview, textarea);
  block.append(over, card);
  return block;
}

function renderCards() {
  editorList.replaceChildren(createIntroBlock());
  for (const article of sortedArticles()) {
    editorList.append(createArticleBlock(article));
  }
  for (const textarea of editorList.querySelectorAll("textarea")) {
    autosize(textarea);
  }
  if (![...editorList.querySelectorAll(".article-block")].some((block) => block.dataset.articleId === activeId)) {
    activeId = "intro";
  }
  setActiveCard(activeId);
}

async function loadContent() {
  const response = await fetch("/api/content");
  if (!response.ok) {
    throw new Error("Inhalt konnte nicht geladen werden.");
  }
  const data = await response.json();
  const parsed = splitMarkdown(data.markdown || "");
  preamble = parsed.preamble;
  articles = parsed.articles;
  renderCards();
}

async function previewNow() {
  const currentRequest = ++requestId;
  setStatus("Speichere und rendere…");
  try {
    const response = await fetch("/api/preview", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        markdown: joinMarkdown(),
        template: templateSelect.value,
      }),
    });
    const data = await response.json();
    if (currentRequest !== requestId) {
      return;
    }
    if (!response.ok || data.error) {
      showError(data.error || "Vorschau fehlgeschlagen.");
      setStatus("Vorschau fehlgeschlagen", true);
      return;
    }
    showPreview(data.html);
    setStatus(`Gespeichert ${formatTime(new Date())}`);
  } catch (error) {
    if (currentRequest !== requestId) {
      return;
    }
    showError(error.message || String(error));
    setStatus("Vorschau fehlgeschlagen", true);
  }
}

function schedulePreview() {
  clearTimeout(previewTimer);
  previewTimer = setTimeout(previewNow, PREVIEW_DELAY_MS);
}

editorPane.addEventListener("scroll", () => {
  window.requestAnimationFrame(updateActiveFromScroll);
}, { passive: true });

previewFrame.addEventListener("load", () => {
  ignoreScrollSync = true;
  scrollPreviewTo(activeId);
  window.setTimeout(() => {
    ignoreScrollSync = false;
  }, 400);
});

templateSelect.addEventListener("change", previewNow);

loadContent()
  .then(previewNow)
  .catch((error) => {
    showError(error.message || String(error));
    setStatus("Inhalt konnte nicht geladen werden", true);
  });
