"""Check every generated local link, fragment, language route and download."""

from __future__ import annotations

import argparse
import json
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit


class Page(HTMLParser):
    def __init__(self, text):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.h1 = [], [], 0
        self.lang = self.viewport = False
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.append(attrs["id"])
        if tag == "h1":
            self.h1 += 1
        if tag == "html":
            self.lang = bool(attrs.get("lang"))
        if tag == "meta" and attrs.get("name") == "viewport":
            self.viewport = True
        for attribute in ("href", "src"):
            if attrs.get(attribute):
                self.links.append(attrs[attribute])


def local_file(root, origin, target, base):
    url = urlsplit(target)
    if url.scheme or url.netloc:
        return None, ""
    path = unquote(url.path)
    if path.startswith("/"):
        if base and not path.startswith(base + "/"):
            raise ValueError(f"Link escapes project base: {target}")
        destination = root / path[len(base) :].lstrip("/")
    else:
        destination = origin.parent / path if path else origin
    if destination.is_dir() or path.endswith("/"):
        destination /= "index.html"
    destination = destination.resolve()
    if not destination.is_relative_to(root.resolve()):
        raise ValueError(f"Link escapes output directory: {target}")
    return destination, unquote(url.fragment)


def validate(root):
    manifest = json.loads((root / "build.json").read_text())
    base = manifest["base"]
    pages = {path.resolve(): Page(path.read_text()) for path in root.rglob("*.html")}
    errors, count = [], 0
    for path, page in pages.items():
        duplicates = [key for key, n in Counter(page.ids).items() if n > 1]
        if duplicates:
            errors.append(f"{path}: duplicate IDs {duplicates}")
        if not page.lang or not page.viewport:
            errors.append(f"{path}: missing language or viewport")
        if "downloads" not in path.parts and page.h1 != 1:
            errors.append(f"{path}: expected one h1, got {page.h1}")
        for link in page.links:
            try:
                destination, fragment = local_file(root, path, link, base)
                if destination is None:
                    continue
                count += 1
                if not destination.is_file():
                    errors.append(f"{path}: missing destination {link}")
                elif (
                    fragment
                    and destination in pages
                    and fragment not in pages[destination].ids
                ):
                    errors.append(f"{path}: missing fragment {link}")
            except ValueError as error:
                errors.append(f"{path}: {error}")
    if len(manifest["routes"]) != 63:
        errors.append("Expected 63 content routes")
    for language in ("zh", "en"):
        for chapter in range(1, 13):
            for prefix in ("", "notes/"):
                if not (
                    root / language / prefix / f"chapter-{chapter:02}" / "index.html"
                ).is_file():
                    errors.append(f"Missing chapter {language}/{prefix}{chapter}")
        with zipfile.ZipFile(
            root / "downloads" / f"in-the-peoples-name-{language}.epub"
        ) as epub:
            if epub.read("mimetype") != b"application/epub+zip":
                errors.append(f"Invalid EPUB mimetype: {language}")
            for name in epub.namelist():
                if name.endswith((".xhtml", ".opf", ".xml", ".ncx")):
                    ET.fromstring(epub.read(name))
    ET.parse(root / "sitemap.xml")
    if errors:
        raise ValueError("\n".join(errors))
    report = {
        "html_files": len(pages),
        "local_links_checked": count,
        "routes": len(manifest["routes"]),
        "status": "passed",
    }
    print(json.dumps(report, indent=2))
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    validate(parser.parse_args().output)
