"""Regressions for citation routing, project paths and faithful Markdown parsing."""

import copy
import tempfile
import unittest
from pathlib import Path

from build import route_links, split_pages
from content import compile_edition, load_document, nodes
from render import Renderer
from validate import Page, local_file


class BookSiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.document = compile_edition("zh")[0]
        cls.pages = split_pages(cls.document)
        cls.renderer = Renderer("/declarations", "https://example.org", {})

    def test_split_notes_retains_every_block(self):
        # Each page title is moved into its page header; all other blocks survive.
        self.assertEqual(len(self.pages), 30)
        self.assertEqual(
            sum(len(p["blocks"]) + 1 for p in self.pages.values()),
            len(self.document["blocks"]),
        )

    def test_exact_citation_return_links(self):
        pages = copy.deepcopy(self.pages)
        route_links(pages, "zh", self.renderer)
        references = {}
        for key, page in pages.items():
            for item in nodes(page["blocks"]):
                if item["t"] == "Link" and item["c"][0][0].startswith("ref-"):
                    anchor = item["c"][2][0].split("#")[-1]
                    references.setdefault(anchor, []).append(
                        "/declarations/zh/" + key + "/#" + item["c"][0][0]
                    )
        self.assertGreater(len(references), 100)
        for anchor, urls in references.items():
            chapter = anchor[2:4]
            note_blocks = pages["notes/chapter-" + chapter]["blocks"]
            html = "".join(b["c"][1] for b in note_blocks if b["t"] == "RawBlock")
            for url in urls:
                self.assertIn(url, html)

    def test_unknown_anchor_fails_build(self):
        pages = copy.deepcopy(self.pages)
        first = next(n for n in nodes(pages["chapter-01"]) if n["t"] == "Link")
        first["c"][2][0] = "#nonexistent"
        with self.assertRaisesRegex(ValueError, "Missing internal"):
            route_links(pages, "zh", self.renderer)

    def test_cjk_adjacent_and_parenthesized_links_survive(self):
        with tempfile.TemporaryDirectory() as folder:
            file = Path(folder) / "sample.md"
            file.write_text("# 标题\n\n中文[来源](https://example.org/a_(b))，后文。\n")
            ast, _ = load_document(file, "sample")
            links = [n["c"][2][0] for n in nodes(ast) if n["t"] == "Link"]
            self.assertEqual(links, ["https://example.org/a_(b)"])

    def test_project_base_and_unicode_fragment(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, fragment = local_file(
                root,
                root / "index.html",
                "/declarations/zh/chapter-01/#%E4%BA%BA",
                "/declarations",
            )
            self.assertEqual(target, (root / "zh/chapter-01/index.html").resolve())
            self.assertEqual(fragment, "人")

    def test_root_base_for_custom_domain(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target, _ = local_file(root, root / "index.html", "/en/", "")
            self.assertEqual(target, (root / "en/index.html").resolve())

    def test_wrong_base_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "escapes project base"):
            local_file(
                Path("/tmp/site"), Path("/tmp/site/index.html"), "/en/", "/declarations"
            )

    def test_escaped_output_path_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "escapes output"):
            local_file(
                Path("/tmp/site"), Path("/tmp/site/index.html"), "../private.txt", ""
            )

    def test_html_parser_collects_ids_and_assets(self):
        page = Page(
            '<html lang="en"><meta name="viewport"><h1 id="a">A</h1><script src="/a.js"></script><a href="#a">A</a></html>'
        )
        self.assertEqual(page.ids, ["a"])
        self.assertEqual(page.links, ["/a.js", "#a"])
        self.assertTrue(page.lang and page.viewport)


if __name__ == "__main__":
    unittest.main()
