"""Read-only presentation of the three original declaration files."""

import json
from dataclasses import dataclass
from html import escape
from pathlib import Path

from content import ROOT, inline_text, pandoc


@dataclass(frozen=True)
class DeclarationEdition:
    language: str
    label: str
    filename: str
    book_language: str
    original_label: str
    source_label: str
    home_label: str
    skip_label: str
    theme_label: str

    @property
    def route(self) -> str:
        return f"original/{self.language}"

    @property
    def source(self) -> Path:
        return ROOT.parent / "mainland-china-liberty" / self.filename

    @property
    def source_url(self) -> str:
        return (
            "https://github.com/my-freedom-foundation/declarations/blob/main/mainland-china-liberty/"
            + self.filename
        )


DECLARATIONS = (
    DeclarationEdition(
        "zh-Hans",
        "简体中文",
        "cn/dec-simplified.md",
        "zh",
        "原始宣言",
        "查看原始文件",
        "返回书籍首页",
        "跳到正文",
        "切换明暗模式",
    ),
    DeclarationEdition(
        "zh-Hant",
        "繁體中文",
        "cn/dec.md",
        "zh",
        "原始宣言",
        "查看原始檔案",
        "返回書籍首頁",
        "跳到正文",
        "切換明暗模式",
    ),
    DeclarationEdition(
        "en",
        "English",
        "en/dec.md",
        "en",
        "Original declaration",
        "View original file",
        "Back to the book",
        "Skip to content",
        "Toggle light or dark mode",
    ),
)


@dataclass
class DeclarationDocument:
    edition: DeclarationEdition
    title: str
    body: str
    signature_label: str
    signatures: str


def load_declaration(edition: DeclarationEdition) -> DeclarationDocument:
    # GFM recognizes the lists without blank lines used by the originals.
    # Disable raw HTML: only Markdown content is admitted into the page template.
    document = json.loads(
        pandoc(
            ["-f", "gfm-raw_html", "-t", "json"],
            edition.source.read_text(encoding="utf-8"),
        )
    )
    blocks = document["blocks"]
    if not blocks or blocks[0]["t"] != "Header":
        raise ValueError(f"Missing declaration title: {edition.source}")
    title = inline_text(blocks[0]["c"][2])
    body = blocks[1:]
    signature_label, signatures = "", []
    for index, block in enumerate(body):
        if block["t"] == "Para" and inline_text(block["c"]) in ("签名：", "簽名："):
            signature_label = inline_text(block["c"])
            signatures, body = body[index + 1 :], body[:index]
            break

    def to_html(parts):
        return pandoc(
            ["-f", "json", "-t", "html5", "--wrap=none"],
            json.dumps({**document, "blocks": parts}, ensure_ascii=False),
        )

    return DeclarationDocument(
        edition, title, to_html(body), signature_label, to_html(signatures)
    )


def render_declaration(document: DeclarationDocument, base: str, origin: str) -> str:
    edition = document.edition

    def url(path=""):
        return base.rstrip("/") + "/" + path.lstrip("/")

    canonical = origin.rstrip("/") + url(edition.route + "/")
    alternates, languages = [], []
    for other in DECLARATIONS:
        path = url(other.route + "/")
        alternates.append(
            f'<link rel="alternate" hreflang="{other.language}" href="{escape(origin.rstrip("/") + path, quote=True)}">'
        )
        current = ' aria-current="page"' if other == edition else ""
        languages.append(
            f'<a href="{path}" lang="{other.language}" hreflang="{other.language}"{current}>{other.label}</a>'
        )
    brand = (
        "Privilege and Freedom"
        if edition.book_language == "en"
        else ("特權與自由" if edition.language == "zh-Hant" else "特权与自由")
    )
    title = escape(document.title)
    signatures = (
        f'<details class="declaration-signatures"><summary>{escape(document.signature_label)}</summary>'
        f'<div class="signature-names">{document.signatures}</div></details>'
        if document.signature_label
        else ""
    )
    return f'''<!doctype html>
<html lang="{edition.language}" class="declaration-theme">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · {escape(brand)}</title>
<meta name="description" content="{escape(edition.original_label + " · " + document.title, quote=True)}">
<meta name="color-scheme" content="light dark"><link rel="canonical" href="{escape(canonical, quote=True)}">
{"".join(alternates)}
<meta property="og:type" content="article"><meta property="og:title" content="{title}"><meta property="og:url" content="{escape(canonical, quote=True)}">
<meta name="twitter:card" content="summary"><link rel="icon" href="{url("assets/favicon.svg")}" type="image/svg+xml">
<link rel="stylesheet" href="{url("assets/reader.css")}"><link rel="stylesheet" href="{url("assets/declaration.css")}">
<script src="{url("assets/reader.js")}" defer></script></head>
<body class="declaration-page"><a class="skip-link" href="#main">{edition.skip_label}</a>
<header class="site-header"><a class="brand" href="{url()}"><span class="brand-mark" aria-hidden="true">P</span><span>{brand}</span></a>
<button class="theme-toggle" type="button" aria-label="{edition.theme_label}" title="{edition.theme_label}" hidden>◐</button></header>
<main id="main" class="declaration-main" tabindex="-1">
<nav class="declaration-languages" aria-label="Language / 语言 / 語言">{"".join(languages)}</nav>
<article class="declaration-sheet">
<p class="declaration-kicker">{edition.original_label}</p>
<div id="declaration-text" class="declaration-text"><h1>{title}</h1>{document.body}{signatures}</div>
<footer class="declaration-source"><a href="{edition.source_url}">{edition.source_label} <span aria-hidden="true">↗</span></a></footer>
</article>
<a class="declaration-return" href="{url()}"><span aria-hidden="true">←</span> {edition.home_label}</a>
</main></body></html>'''
