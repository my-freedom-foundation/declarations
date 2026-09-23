# The book website

## Reading and maintenance

The authoritative website manuscripts are in `manuscript/zh/` and `manuscript/en/`. The initial import uses the complete 17 September 2026 reading editions. `provenance.json` records the source commit and hashes; it is an import record, not a restriction on later revisions. The only import transformation redirects research-register links to the corresponding reader notes. No prose was rewritten for the website.

To revise the book, edit the Markdown chapter and its matching notes in `93-notes.md`. Keep note identifiers such as `CH07-F01` stable. A chapter's route uses its number, so changing its title does not break shared chapter links. Section links use heading-derived identifiers; preserve headings when keeping an existing section link is important.

## Build and preview

Requires Python **3.12+** and Pandoc **2.11+**. There is no npm application, external font request, analytics, or production package dependency. JavaScript enhances theme selection and copying links; reading, navigation, and sources also work without it.

From the repository root:

```sh
python3 -m compileall -q book/site
python3 -m unittest discover -s book/site -p 'test_*.py'
python3 book/site/build.py
python3 book/site/validate.py _site
```

For a local preview without the project URL prefix:

```sh
python3 book/site/build.py --base '' --output /tmp/declarations-book-preview
python3 -m http.server 8769 --directory /tmp/declarations-book-preview --bind 127.0.0.1
```

Open http://127.0.0.1:8769/. Generated output belongs in `_site/` or a temporary directory and is not committed. `build.py --origin https://books.example.com --base ''` also supports a custom-domain build; configure the matching Pages domain before deploying it.

## GitHub Pages

1. A repository administrator opens **Settings → Pages → Build and deployment → Source → GitHub Actions**.
2. Push the book and workflow to `main`, or run **Actions → Publish the book → Run workflow**.
3. The build runs the citation/URL tests, creates both language editions, and validates local links and downloads before uploading `_site/`.
4. The deployment job publishes that artifact. Pull requests build and validate without deploying.

The configured project URL is `https://my-freedom-foundation.github.io/declarations/`. Paths include:

| Content | Path |
| --- | --- |
| Language selection | `/declarations/` |
| Chinese / English contents | `/declarations/zh/`, `/declarations/en/` |
| Chapter 7 | `/declarations/zh/chapter-07/` |
| Corresponding English chapter | `/declarations/en/chapter-07/` |
| Chapter 7 sources | `/declarations/zh/notes/chapter-07/` |
| A particular source note | `/declarations/zh/notes/chapter-07/#ch07-f01` |
| EPUB download | `/declarations/downloads/privilege-and-freedom-zh.epub` |
| Single-page reading edition | `/declarations/downloads/privilege-and-freedom-zh.html` |

Only `_site/` is deployed. Existing declarations remain unchanged and are linked to their GitHub locations. Source attribution and qualifications in the manuscripts are preserved; linked external sources may change independently of this repository.

The title changed to **Privilege and Freedom: Who Makes the Rules, Who Pays the Price / 特权与自由：谁制定规则，谁承担代价** on 23 September 2026. Downloads use `privilege-and-freedom-{en,zh}`; the previous `in-the-peoples-name-{en,zh}` URLs serve identical updated copies so shared links keep working. Chapter URLs and the manuscript cutoff are unchanged.

## Reader experience and acceptance criteria

**Reader story:** a Chinese- or English-speaking reader arrives through a shared chapter link, reads comfortably on a phone or desktop, checks a citation, and continues reading or switches to the corresponding chapter in the other language.

**Visual direction:** warm paper, dark text, one restrained accent, a narrow reading column, generous line spacing, and a quiet table of contents. The homepage has one choice per edition. Chapter pages prioritize reading and continuing to the next chapter. Native page navigation resets scroll; citation links and return links target the relevant passage. Mobile contents expand in place.

Acceptance evidence:

- Every manuscript is represented; twelve chapters and twelve note pages per language.
- Chapter URLs do not depend on titles. Language switches preserve the route.
- Each citation reaches an existing note; note return links reach their exact references.
- Layout fits 320 px phones through large desktop screens; wide tables scroll within their own region.
- Keyboard navigation, visible focus, skip links, reduced motion, dark mode, and a usable no-JavaScript reading experience.
- Both EPUBs and standalone HTML downloads are built from the same input as the website.
- All local assets, route links, fragments, EPUB XML, and sitemap XML pass validation.
- A read-only Codex review and browser checks precede delivery. See `VERIFICATION.md` for the implementation's recorded results.

## Implementation boundaries

`site/content.py` handles Markdown and full-edition assembly; `site/build.py` handles page splitting, citation backlinks and output; `site/render.py` owns localized page templates and navigation. `site/validate.py` checks generated artifacts. Styling and browser enhancements are local assets. The build uses Pandoc's `markdown-smart` reader to preserve CJK-adjacent links and parenthesized destinations.
