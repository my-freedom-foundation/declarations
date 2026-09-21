"""Assemble the two reading editions from the maintained Markdown manuscripts."""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "downloads"
DATE = "2026-09-16"
LANGUAGES = {
    "zh": ("zh-CN", "以人民之名", "特权、革命与不受约束的权力", "目录", "完整阅读稿"),
    "en": (
        "en-US",
        "In the People's Name",
        "Privilege, Revolution, and Unaccountable Power",
        "Contents",
        "Complete reading draft",
    ),
}
SOURCE = re.compile(r"CH(\d{2})-SOURCES\.md$")
NOTE = re.compile(r"CH(\d{2})-([A-Z]+\d{2})$")
LINK = re.compile(r"\[[^]\n]*\]\(((?:[^()\n]|\([^()\n]*\))*)\)")


def pandoc(arguments: list[str], text: str) -> str:
    result = subprocess.run(
        ["pandoc", *arguments], input=text, text=True, capture_output=True, check=True
    )
    if result.stderr.strip():
        print(result.stderr.strip())
    return result.stdout


def nodes(value):
    """Yield AST nodes without making assumptions about nested tables or spans."""
    if isinstance(value, dict):
        if "t" in value:
            yield value
        for child in value.values():
            yield from nodes(child)
    elif isinstance(value, list):
        for child in value:
            yield from nodes(child)


def inline_text(value) -> str:
    return "".join(
        item["c"] if item["t"] == "Str" else " "
        for item in nodes(value)
        if item["t"] in ("Str", "Space", "SoftBreak", "LineBreak")
    )


def documents(language: str) -> list[tuple[Path, str]]:
    folder = ROOT / "manuscript" / language
    result = [
        (folder / "00-preface.md", "preface"),
        (folder / "00-reading-guide.md", "reading-guide"),
    ]
    for number in range(1, 13):
        matches = sorted(folder.glob(f"{number:02}-*.md"))
        if len(matches) != 1:
            raise ValueError(
                f"Expected one chapter {number} in {language}, got {matches}"
            )
        result.append((matches[0], f"chapter-{number:02}"))
    for filename, key in [
        ("90-chronology.md", "chronology"),
        ("91-glossary.md", "glossary"),
        ("92-declaration-annotated.md", "declaration"),
        ("93-notes.md", "notes"),
    ]:
        result.append((folder / filename, key))
    return result


def load_document(path: Path, key: str):
    text = path.read_text(encoding="utf-8")
    # Editorial version lines remain in source files, but need not repeat in a book.
    text = re.sub(r"^\*[^\n]*v0\.\d+[^\n]*\*\n", "", text, flags=re.MULTILINE)
    # Pandoc 2.11's CommonMark reader misparses some CJK-adjacent links.
    document = json.loads(pandoc(["-f", "markdown-smart", "-t", "json"], text))
    explicit_links = LINK.findall(text)
    parsed_links = [
        item["c"][2][0] for item in nodes(document["blocks"]) if item["t"] == "Link"
    ]
    if explicit_links != parsed_links:
        raise ValueError(f"Link parsing changed source destinations in {path}")
    anchors = {"": key}
    notes_chapter = 0
    first = True
    for item in nodes(document["blocks"]):
        if item["t"] != "Header":
            continue
        level, attributes, inlines = item["c"]
        original = attributes[0]
        label = inline_text(inlines)
        if first:
            if level != 1:
                raise ValueError(f"Missing document title: {path}")
            new_id = key
            first = False
        elif key == "notes" and level == 2:
            notes_chapter += 1
            new_id = f"notes-ch{notes_chapter:02}"
        elif key == "notes" and NOTE.fullmatch(label):
            new_id = label.lower()
        else:
            new_id = f"{key}-{original}"
        anchors[original] = new_id
        anchors[new_id] = new_id
        attributes[0] = new_id
    if first or (key == "notes" and notes_chapter != 12):
        raise ValueError(f"Unexpected heading structure: {path}")
    return document, anchors


def resolve_link(origin: Path, target: str, anchors: dict, note_ids: set[str]) -> str:
    parts = urlsplit(target)
    if parts.scheme in ("https", "http", "mailto"):
        return target
    if parts.scheme or parts.netloc or parts.query:
        raise ValueError(f"Unsupported reading-edition link in {origin.name}: {target}")
    path = (origin.parent / unquote(parts.path)).resolve() if parts.path else origin
    fragment = unquote(parts.fragment)
    source = SOURCE.fullmatch(path.name)
    if source and path.parent == ROOT / "research":
        chapter = source.group(1)
        destination = (
            f"ch{chapter}-{fragment.lower()}" if fragment else f"notes-ch{chapter}"
        )
        if destination not in note_ids:
            raise ValueError(f"Source has no reader note: {target}")
        return f"#{destination}"
    if path not in anchors or fragment not in anchors[path]:
        raise ValueError(f"Unmapped internal link in {origin.name}: {target}")
    return "#" + anchors[path][fragment]


def compile_edition(language: str) -> tuple[dict, dict]:
    loaded = []
    anchor_maps = {}
    manifest = []
    for path, key in documents(language):
        document, anchors = load_document(path, key)
        loaded.append((path, document))
        anchor_maps[path] = anchors
        manifest.append({"file": str(path.relative_to(ROOT)), "anchor": key})
    note_ids = set(anchor_maps[loaded[-1][0]].values())
    blocks = []
    for path, document in loaded:
        for item in nodes(document["blocks"]):
            if item["t"] == "Link":
                target = item["c"][2][0]
                item["c"][2][0] = resolve_link(path, target, anchor_maps, note_ids)
                if re.fullmatch(r"\d+", inline_text(item["c"][1])):
                    item["c"][0][1].append("citation")
        for block in document["blocks"]:
            blocks.append(block)
            if block["t"] == "Header" and re.fullmatch(
                r"notes-ch\d{2}", block["c"][1][0]
            ):
                chapter = int(block["c"][1][0][-2:])
                label = (
                    f"返回第{chapter}章"
                    if language == "zh"
                    else f"Return to Chapter {chapter}"
                )
                blocks.append(
                    {
                        "t": "Para",
                        "c": [
                            {
                                "t": "Link",
                                "c": [
                                    ["", ["return-link"], []],
                                    [{"t": "Str", "c": label}],
                                    [f"#chapter-{chapter:02}", ""],
                                ],
                            }
                        ],
                    }
                )
    locale, title, subtitle, toc, edition = LANGUAGES[language]
    metadata = {
        key: {"t": "MetaString", "c": value}
        for key, value in {
            "title": title,
            "subtitle": subtitle,
            "lang": locale,
            "date": DATE,
            "toc-title": toc,
            "edition": edition,
            "identifier": f"urn:mainland-china-liberty:{language}:{DATE}:reading-v1",
        }.items()
    }
    document = {
        "pandoc-api-version": loaded[0][1]["pandoc-api-version"],
        "meta": metadata,
        "blocks": blocks,
    }
    return document, {
        "language": locale,
        "documents": manifest,
        "source_groups": len(
            [x for x in note_ids if re.fullmatch(r"ch\d{2}-[a-z]+\d{2}", x)]
        ),
    }
