"""Generate the bilingual GitHub Pages site and complete reading downloads."""

from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
from html import escape
from pathlib import Path
from urllib.parse import quote

from content import LANGUAGES, ROOT, compile_edition, inline_text, nodes, pandoc
from render import TEXT, Renderer

SITE = Path(__file__).resolve().parent


def split_pages(document):
    pages, current = {}, None
    for block in document["blocks"]:
        if block["t"] == "Header":
            level, attr, text = block["c"]
            if level == 1:
                current = attr[0]
                pages[current] = {
                    "title": inline_text(text),
                    "anchor": attr[0],
                    "blocks": [],
                }
                continue
            if current and current.startswith("notes") and level == 2:
                current = "notes/chapter-" + attr[0][-2:]
                pages[current] = {
                    "title": inline_text(text),
                    "anchor": attr[0],
                    "blocks": [],
                }
                continue
        if current is None:
            raise ValueError("Content before first heading")
        pages[current]["blocks"].append(copy.deepcopy(block))
    if len(pages) != 30:
        raise ValueError(f"Expected 30 pages per language, got {len(pages)}")
    return pages


def route_links(pages, lang, renderer):
    destinations = {}
    for key, page in pages.items():
        route = renderer.url(f"{lang}/{key}/")
        destinations[page["anchor"]] = route
        for item in nodes(page["blocks"]):
            if item["t"] == "Header":
                destinations[item["c"][1][0]] = route + "#" + quote(item["c"][1][0])
    references = {}
    for key, page in pages.items():
        for item in nodes(page["blocks"]):
            if item["t"] != "Link":
                continue
            attr, label, target = item["c"]
            if not target[0].startswith("#"):
                continue
            anchor = target[0][1:]
            if anchor not in destinations:
                raise ValueError(f"Missing internal destination: {anchor}")
            target[0] = destinations[anchor]
            if re.fullmatch(r"ch\d{2}-[a-z]+\d{2}", anchor):
                refs = references.setdefault(anchor, [])
                reference_id = f"ref-{anchor}-{len(refs) + 1}"
                attr[0] = reference_id
                attr[2].append(
                    [
                        "aria-label",
                        ("注释 " if lang == "zh" else "Note ") + inline_text(label),
                    ]
                )
                refs.append(renderer.url(f"{lang}/{key}/") + "#" + reference_id)
    for key, page in pages.items():
        if not key.startswith("notes/"):
            continue
        blocks, current = [], None

        def add_backlinks(note_id, destination_blocks):
            if note_id in references:
                links = " · ".join(
                    f'<a href="{escape(url, quote=True)}">{TEXT[lang]["return_note"]}{" " + str(i + 1) if len(references[note_id]) > 1 else ""} ↑</a>'
                    for i, url in enumerate(references[note_id])
                )
                destination_blocks.append(
                    {
                        "t": "RawBlock",
                        "c": ["html", f'<p class="note-backlinks">{links}</p>'],
                    }
                )

        for block in page["blocks"]:
            if block["t"] == "Header":
                add_backlinks(current, blocks)
                current = block["c"][1][0]
                block["c"][0] = 2
            blocks.append(block)
        add_backlinks(current, blocks)
        page["blocks"] = blocks
    return destinations


def body_html(document, page, language):
    ast = {
        "pandoc-api-version": document["pandoc-api-version"],
        "meta": {},
        "blocks": page["blocks"],
    }
    html = pandoc(
        ["-f", "json", "-t", "html5", "--wrap=none"],
        json.dumps(ast, ensure_ascii=False),
    )
    table_label = (
        "时间线表格，可横向滚动"
        if language == "zh"
        else "Chronology table, scroll horizontally"
    )
    html = re.sub(
        r"<table([^>]*)>",
        f'<div class="table-scroll" role="region" aria-label="{table_label}" tabindex="0"><table\\1>',
        html,
    )
    return html.replace("</table>", "</table></div>")


def download(document, language, output):
    text = json.dumps(document, ensure_ascii=False)
    stem = output / f"privilege-and-freedom-{language}"
    for extension, args in [
        (
            "epub",
            ["-t", "epub3", "--epub-chapter-level=1", "--css", str(SITE / "epub.css")],
        ),
        (
            "html",
            [
                "-t",
                "html5",
                "--section-divs",
                "--template",
                str(SITE / "download.html"),
            ],
        ),
    ]:
        pandoc(
            [
                "-f",
                "json",
                "--standalone",
                "--toc",
                "--toc-depth=1",
                *args,
                "-o",
                str(stem.with_suffix("." + extension)),
            ],
            text,
        )
        # Existing download URLs remain valid after the title change.
        shutil.copyfile(
            stem.with_suffix("." + extension),
            output / f"in-the-peoples-name-{language}.{extension}",
        )


def build(
    output, base="/declarations", origin="https://my-freedom-foundation.github.io"
):
    base = base.rstrip("/")
    if base and (not re.fullmatch(r"/[a-zA-Z0-9_/-]+", base) or ".." in base):
        raise ValueError("Base must be a root-relative URL path")
    output.mkdir(parents=True, exist_ok=True)
    docs = {lang: compile_edition(lang)[0] for lang in LANGUAGES}
    pages = {lang: split_pages(doc) for lang, doc in docs.items()}
    catalogs = {
        lang: [
            (key, page["title"])
            for key, page in edition.items()
            if not key.startswith("notes/")
        ]
        for lang, edition in pages.items()
    }
    renderer = Renderer(base, origin.rstrip("/"), catalogs)
    routes = []

    def write(path, html):
        file = output / path / "index.html"
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(html, encoding="utf-8")
        routes.append(path)

    write("", renderer.home())
    (output / "downloads").mkdir(exist_ok=True)
    for lang, edition in pages.items():
        route_links(edition, lang, renderer)
        write(lang, renderer.contents(lang))
        for key, page in edition.items():
            html = body_html(docs[lang], page, lang)
            sections = [
                (n["c"][1][0], inline_text(n["c"][2]))
                for n in nodes(page["blocks"])
                if n["t"] == "Header" and n["c"][0] == 2
            ]
            if key == "notes":
                links = "".join(
                    f'<li><a href="{renderer.url(lang + "/notes/" + k + "/")}">{escape(title)}</a></li>'
                    for k, title in catalogs[lang]
                    if k.startswith("chapter-")
                )
                html += f'<ol class="notes-index">{links}</ol>'
            write(
                f"{lang}/{key}",
                renderer.article(lang, key, page["title"], html, sections),
            )
        download(docs[lang], lang, output / "downloads")
    shutil.copytree(SITE / "assets", output / "assets", dirs_exist_ok=True)
    (output / ".nojekyll").touch()
    missing = (
        '<section class="not-found"><p class="eyebrow">404</p><h1>这一页不在这里。<br><span lang="en">This page is missing.</span></h1><p><a href="'
        + renderer.url("zh/")
        + '">中文目录 →</a></p><p><a href="'
        + renderer.url("en/")
        + '">English contents →</a></p></section>'
    )
    (output / "404.html").write_text(
        renderer.shell("zh", "home", "Page not found", missing, False)
    )
    sitemap = (
        '<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        + "".join(
            "<url><loc>"
            + escape(origin.rstrip("/") + renderer.url(route + "/"))
            + "</loc></url>"
            for route in routes
        )
        + "</urlset>"
    )
    (output / "sitemap.xml").write_text(sitemap)
    (output / "robots.txt").write_text(
        "User-agent: *\nAllow: /\nSitemap: "
        + origin.rstrip("/")
        + renderer.url("sitemap.xml")
        + "\n"
    )
    (output / "build.json").write_text(
        json.dumps(
            {
                "base": base,
                "routes": routes,
                "revision": "2026-09-17",
                "languages": list(LANGUAGES),
            },
            indent=2,
        )
        + "\n"
    )
    print(f"Built {len(routes)} pages, a 404 page, and 4 reading downloads in {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT.parent / "_site")
    parser.add_argument("--base", default="/declarations")
    parser.add_argument("--origin", default="https://my-freedom-foundation.github.io")
    args = parser.parse_args()
    build(args.output, args.base, args.origin)
