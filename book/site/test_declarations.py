"""The original declarations must survive presentation changes verbatim."""

import hashlib
import json
import re
import unittest
from html.parser import HTMLParser

from content import inline_text, nodes, pandoc
from declarations import DECLARATIONS, load_declaration, render_declaration
from render import Renderer


class DocumentText(HTMLParser):
    def __init__(self, html):
        super().__init__(convert_charrefs=True)
        self.depth = 0
        self.text = []
        self.links = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if attrs.get("id") == "declaration-text":
            self.depth = 1
        elif self.depth and tag not in ("br", "hr", "img", "wbr"):
            self.depth += 1
        if self.depth and tag == "a":
            self.links.append(attrs["href"])

    def handle_endtag(self, tag):
        if self.depth:
            self.depth -= 1

    def handle_data(self, data):
        if self.depth:
            self.text.append(data)


class DeclarationTests(unittest.TestCase):
    def test_original_text_links_and_lists_survive_rendering(self):
        for edition in DECLARATIONS:
            with self.subTest(language=edition.language):
                before = hashlib.sha256(edition.source.read_bytes()).hexdigest()
                document = load_declaration(edition)
                html = render_declaration(
                    document, "/declarations", "https://example.org"
                )
                parsed = DocumentText(html)
                original = json.loads(
                    pandoc(["-f", "gfm", "-t", "json"], edition.source.read_text())
                )
                normalize = lambda value: re.sub(r"\s+", "", value)
                self.assertEqual(
                    normalize("".join(parsed.text)),
                    normalize(inline_text(original["blocks"])),
                )
                original_links = [
                    n["c"][2][0] for n in nodes(original) if n["t"] == "Link"
                ]
                self.assertEqual(parsed.links, original_links)
                lists = [
                    n
                    for n in nodes(original)
                    if n["t"] in ("BulletList", "OrderedList")
                ]
                self.assertEqual(
                    [
                        len(n["c"] if n["t"] == "BulletList" else n["c"][1])
                        for n in lists
                    ],
                    [3, 16],
                )
                self.assertEqual(html.count("<li>"), 19)
                self.assertEqual(
                    before, hashlib.sha256(edition.source.read_bytes()).hexdigest()
                )

    def test_language_routes_metadata_and_source_links(self):
        for base in ("", "/declarations"):
            for edition in DECLARATIONS:
                with self.subTest(base=base, language=edition.language):
                    html = render_declaration(
                        load_declaration(edition), base, "https://example.org"
                    )
                    self.assertIn(f'<html lang="{edition.language}"', html)
                    self.assertIn(
                        f'href="https://example.org{base}/{edition.route}/"', html
                    )
                    for alternate in DECLARATIONS:
                        self.assertIn(f'href="{base}/{alternate.route}/"', html)
                    self.assertIn(edition.source_url, html)
                    self.assertEqual(html.count('aria-current="page"'), 1)
                    self.assertEqual(html.count("<h1"), 1)
                    self.assertNotIn("/Users/", html)

    def test_only_supplied_signature_sections_are_disclosed(self):
        for edition in DECLARATIONS:
            html = render_declaration(
                load_declaration(edition), "", "https://example.org"
            )
            self.assertEqual(
                '<details class="declaration-signatures">' in html,
                edition.language != "en",
            )

    def test_home_links_to_all_three_reading_pages(self):
        renderer = Renderer(
            "/declarations", "https://example.org", {"en": [], "zh": []}
        )
        html = renderer.home()
        for edition in DECLARATIONS:
            self.assertIn(f'href="/declarations/{edition.route}/"', html)
            self.assertNotIn(edition.source_url, html)


if __name__ == "__main__":
    unittest.main()
