"""Accessible page templates and navigation, independent of manuscript parsing."""

import re
from html import escape as esc

TEXT = {
    "zh": {
        "title": "特权与自由",
        "subtitle": "谁制定规则，谁承担代价",
        "contents": "全书目录",
        "start": "开始阅读",
        "previous": "上一节",
        "following": "下一节",
        "tools": "阅读工具",
        "copy": "复制本章链接",
        "copied": "链接已复制",
        "failed": "请复制浏览器地址栏中的链接",
        "theme": "切换明暗模式",
        "section": "本页内容",
        "skip": "跳到正文",
        "notes": "注释与来源",
        "download": "下载中文版 EPUB",
        "edition": "中文阅读版",
        "home": "书籍首页",
        "front": "开始之前",
        "chapters": "正文 · 十二章",
        "back": "附录与注释",
        "updated": "修订于 2026 年 9 月 17 日",
        "return_note": "返回引用处",
        "return_chapter": "返回本章",
    },
    "en": {
        "title": "Privilege and Freedom",
        "subtitle": "Who Makes the Rules, Who Pays the Price",
        "contents": "Contents",
        "start": "Start reading",
        "previous": "Previous",
        "following": "Next",
        "tools": "Reading tools",
        "copy": "Copy chapter link",
        "copied": "Link copied",
        "failed": "Please copy the URL from your address bar",
        "theme": "Toggle light or dark mode",
        "section": "On this page",
        "skip": "Skip to content",
        "notes": "Notes & sources",
        "download": "Download English EPUB",
        "edition": "English edition",
        "home": "Book home",
        "front": "Before you begin",
        "chapters": "The twelve chapters",
        "back": "Appendices & notes",
        "updated": "Revised 17 September 2026",
        "return_note": "Back to reference",
        "return_chapter": "Back to chapter",
    },
}


def short_title(title):
    return re.split(r"\u3000| · ", title, maxsplit=1)[-1]


class Renderer:
    def __init__(self, base, origin, catalogs):
        self.base, self.origin, self.catalogs = base, origin, catalogs

    def url(self, path=""):
        return self.base + "/" + path.lstrip("/")

    def nav(self, lang, current, full=False):
        t = TEXT[lang]
        groups = [
            (t["front"], self.catalogs[lang][:2]),
            (t["chapters"], self.catalogs[lang][2:14]),
            (t["back"], self.catalogs[lang][14:]),
        ]
        parts = []
        for label, entries in groups:
            links = []
            for key, title in entries:
                active = ' aria-current="page"' if key == current else ""
                number = key.split("-")[-1] if key.startswith("chapter-") else "·"
                links.append(
                    f'<li><a href="{self.url(f"{lang}/{key}/")}"{active}>'
                    f'<span class="nav-number" aria-hidden="true">{number}</span>'
                    f"<span>{esc(short_title(title))}</span>{'<span aria-hidden="true">↗</span>' if full else ''}</a></li>"
                )
            parts.append(
                f'<section class="nav-group"><h2>{label}</h2><ol>{"".join(links)}</ol></section>'
            )
        return "".join(parts)

    def shell(self, lang, key, title, main, sidebar=True):
        t = TEXT[lang]
        path = f"{lang}/{key}/" if key else f"{lang}/"
        if key == "home":
            path = ""
        alternate = "en" if lang == "zh" else "zh"
        alt_path = f"{alternate}/{key}/" if key and key != "home" else f"{alternate}/"
        canonical = self.origin + self.url(path)
        description = t["subtitle"]
        nav = self.nav(lang, key)
        side = (
            f'<aside class="sidebar"><a class="contents-heading" href="{self.url(lang + "/")}">{t["contents"]}</a><nav aria-label="{t["contents"]}">{nav}</nav><a class="sidebar-download" href="{self.url("downloads/privilege-and-freedom-" + lang + ".epub")}" download>{t["download"]} ↓</a></aside>'
            if sidebar
            else ""
        )
        mobile = (
            f'<details class="mobile-contents"><summary>{t["contents"]}</summary><nav aria-label="{t["contents"]}">{nav}</nav></details>'
            if sidebar
            else ""
        )
        return f'''<!doctype html>
<html lang="{"zh-CN" if lang == "zh" else "en"}">
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)} · {esc(t["title"])}</title>
<meta name="description" content="{esc(description, quote=True)}"><meta name="color-scheme" content="light dark">
<link rel="canonical" href="{canonical}"><link rel="alternate" hreflang="{alternate}" href="{self.origin + self.url(alt_path)}">
<meta property="og:type" content="article"><meta property="og:title" content="{esc(title, quote=True)}"><meta property="og:description" content="{esc(description, quote=True)}"><meta property="og:url" content="{canonical}">
<meta name="twitter:card" content="summary"><link rel="icon" href="{self.url("assets/favicon.svg")}" type="image/svg+xml">
<link rel="stylesheet" href="{self.url("assets/reader.css")}"><script src="{self.url("assets/reader.js")}" defer></script></head>
<body><a class="skip-link" href="#main">{t["skip"]}</a>
<header class="site-header"><a class="brand" href="{self.url()}"><span class="brand-mark" aria-hidden="true">P</span><span>{esc(t["title"])}</span></a>
<nav class="header-actions" aria-label="{t["tools"]}"><a href="{self.url(alt_path)}" lang="{alternate}" hreflang="{alternate}">{"English" if lang == "zh" else "中文"}</a><button class="theme-toggle" type="button" aria-label="{t["theme"]}" title="{t["theme"]}" hidden>◐</button></nav></header>
<div class="{"reading-layout" if sidebar else "wide-layout"}">{side}<main id="main" tabindex="-1">{mobile}{main}</main></div>
<footer class="site-footer"><a href="{self.url()}">{t["home"]}</a><span>{t["updated"]}</span><a href="https://github.com/my-freedom-foundation/declarations">GitHub ↗</a></footer>
</body></html>'''

    def contents(self, lang):
        t = TEXT[lang]
        body = f'''<div class="contents-page"><p class="eyebrow">{t["edition"]}</p><h1>{esc(t["title"])}</h1><p class="subtitle">{t["subtitle"]}</p>
<div class="edition-actions"><a class="primary-link" href="{self.url(lang + "/preface/")}">{t["start"]} <span aria-hidden="true">→</span></a><a href="{self.url("downloads/privilege-and-freedom-" + lang + ".epub")}" download>{t["download"]} ↓</a></div>
<nav class="full-contents" aria-label="{t["contents"]}">{self.nav(lang, "", True)}</nav></div>'''
        return self.shell(lang, "", t["contents"], body, False)

    def home(self):
        body = f'''<section class="book-cover"><p class="eyebrow">LIBERTY · POWER · RESPONSIBILITY</p>
<div class="cover-rule"></div><h1>特权与自由</h1><p class="cover-subtitle">谁制定规则，谁承担代价</p>
<div lang="en" class="english-title"><h2>Privilege and Freedom</h2><p>Who Makes the Rules, Who Pays the Price</p></div>
<div class="edition-choices"><a class="edition-choice" href="{self.url("zh/")}"><span>中文阅读版</span><strong>阅读本书 <span aria-hidden="true">→</span></strong><small>十二章 · 注释与来源</small></a><a class="edition-choice" href="{self.url("en/")}" lang="en"><span>English edition</span><strong>Read the book <span aria-hidden="true">→</span></strong><small>Twelve chapters · Notes & sources</small></a></div>
</section><section class="about-book"><div><p class="eyebrow">从一份宣言开始</p><p>从特权与平等，到权力与责任。这本书沿着历史中的自由问题展开，思考个人如何面对不受约束的权力。</p><p lang="en">From privilege and equality to power and responsibility: a book about freedom, and the individual’s place in the history of unaccountable power.</p></div><div class="original-links"><h2>最初的宣言 <span lang="en">The original declaration</span></h2><a href="https://github.com/my-freedom-foundation/declarations/blob/main/mainland-china-liberty/cn/dec-simplified.md">简体中文 ↗</a><a href="https://github.com/my-freedom-foundation/declarations/blob/main/mainland-china-liberty/cn/dec.md">繁體中文 ↗</a><a href="https://github.com/my-freedom-foundation/declarations/blob/main/mainland-china-liberty/en/dec.md" lang="en">English ↗</a></div></section>'''
        return self.shell(
            "zh", "home", "特权与自由 / Privilege and Freedom", body, False
        )

    def article(self, lang, key, title, html, sections):
        t = TEXT[lang]
        is_notes = key.startswith("notes/")
        chapter = re.fullmatch(r"chapter-(\d+)", key)
        label = (
            (
                f"第 {int(chapter[1])} 章 / 12"
                if lang == "zh"
                else f"CHAPTER {int(chapter[1]):02} / 12"
            )
            if chapter
            else (t["notes"] if is_notes else t["edition"])
        )
        contents = "".join(
            f'<li><a href="#{esc(anchor, quote=True)}">{esc(text)}</a></li>'
            for anchor, text in sections
        )
        outline = (
            f'<details class="page-outline"><summary>{t["section"]}</summary><ol>{contents}</ol></details>'
            if contents
            else ""
        )
        entries = self.catalogs[lang]
        index = next((i for i, (k, _) in enumerate(entries) if k == key), None)
        nav = []
        if is_notes:
            destination = key.split("/")[1]
            nav.append(
                f'<a href="{self.url(lang + "/" + destination + "/")}">← {t["return_chapter"]}</a>'
            )
        elif index is not None:
            for delta, direction in [(-1, "previous"), (1, "following")]:
                other = index + delta
                if 0 <= other < len(entries):
                    k, heading = entries[other]
                    nav.append(
                        f'<a class="{direction}" href="{self.url(lang + "/" + k + "/")}"><span>{t[direction]} {"→" if delta == 1 else "←"}</span><strong>{esc(short_title(heading))}</strong></a>'
                    )
        actions = f'<div class="article-actions"><button data-copy data-copied="{t["copied"]}" data-failed="{t["failed"]}" hidden>{t["copy"]}</button><span class="copy-status" role="status" aria-live="polite"></span></div>'
        if chapter:
            actions += f'<a class="chapter-notes-link" href="{self.url(lang + "/notes/" + key + "/")}">{t["notes"]} ↗</a>'
        body = f'<article class="article"><header class="article-header"><p class="eyebrow">{label}</p><h1>{esc(short_title(title))}</h1><div class="article-tools">{actions}</div></header>{outline}<div class="prose">{html}</div><nav class="chapter-navigation" aria-label="{t["contents"]}">{"".join(nav)}</nav><a class="back-to-contents" href="{self.url(lang + "/")}">{t["contents"]} ↑</a></article>'
        return self.shell(lang, key, title, body)
