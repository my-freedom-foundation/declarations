# Implementation verification — 21 September 2026

## Scope

Separate Chinese and English reading editions, chapter URLs, chapter navigation, corresponding-language links, per-chapter source notes with precise reference backlinks, responsive layout, light/dark themes, link copying, and EPUB/HTML downloads. Original declaration files are unchanged.

## Automated checks

- Python formatting (Ruff): passed.
- Python lint (Ruff): passed.
- Python type checking (mypy): passed, five source files.
- Python compilation and JavaScript syntax: passed.
- Nine regression tests: passed, covering CJK/parenthesized source links, exact citation return links, page splitting, missing-anchor errors, project/custom-domain paths, traversal rejection and HTML parsing.
- Build: 63 content routes, one 404 page, two EPUBs and two complete HTML reading editions.
- Output validation: 66 HTML files; all 5,436 local asset/navigation/fragment links passed. EPUB XML and sitemap XML parsed successfully.
- All 36 import hashes matched; parsed visible prose is identical to the original editions.
- JSON and GitHub Actions YAML structure: passed.
- Git whitespace check: passed.

Verification tools were installed temporarily outside the repository; no production dependency was added. The normal build uses Python's standard library and Pandoc.

## Browser evidence

Playwright/Chrome checked the homepage, English contents, Chinese Chapter 7, English Chapter 11, Chinese chronology, and English Chapter 11 notes at widths **320, 390, 768 and 1440 px**: 24 combinations, with no page-level horizontal overflow, missing main content, duplicate page titles, or failed page responses.

The following interactions passed:

- Citation → corresponding note → exact reference in the chapter, with the reference visible after return.
- Chinese Chapter 7 → English Chapter 7.
- Next/previous chapter navigation, including scroll reset on the next chapter.
- Light/dark toggle and persistence after reload.
- Copying the current chapter URL without a fragment.
- Expanding the mobile table of contents and navigating to another chapter.
- Mobile navigation with JavaScript disabled.
- Wide chronology table contained in its own horizontal scrolling region.
- First keyboard Tab reaches the skip link; activating it focuses the main content.
- The actual repository build works under `/declarations/`, including language links and notes.
- Both EPUB download endpoints return HTTP 200 and nonempty files.

Desktop light, desktop dark, and mobile layouts were visually inspected. Local screenshots are in `output/playwright/` (ignored by Git): `home-desktop.png`, `home-mobile.png`, `chapter-desktop.png`, `chapter-dark-desktop.png`, `chapter-mobile.png`, and `english-small-phone.png`.

## Read-only review

A Codex review ran with `sandbox_mode="read-only"` using GPT-5.5 (the installed CLI could not run its default newer model). It found one low-priority navigation-label issue: the notes-page footer returned to the chapter root while saying “Back to reference.” This was corrected to “Back to chapter” / “返回本章”; individual source-note backlinks still return to exact references. The corrected route and both labels were rechecked. No blocking findings remain.

## Publishing status

Local implementation, verification, and read-only review are complete. Live deployment has not run. The GitHub CLI account available during implementation, `Thomas-sls`, reports read-only access to this public repository; SSH authentication also fails. An account with repository write access and Pages administration permission is required to push and enable GitHub Actions as the Pages source. No X posts were created.

External-source availability and the book's factual assertions were not re-audited in this website implementation. Existing manuscript wording and qualifications were retained.


## Title rename — 23 September 2026

Updated the website and both language editions to **Privilege and Freedom: Who Makes the Rules, Who Pays the Price / 特权与自由：谁制定规则，谁承担代价**. Chapter routes and body text are unchanged. Downloads now use `privilege-and-freedom-{en,zh}`; old URLs serve identical updated copies.

Verification: Ruff formatting and lint pass; mypy passes all five source files; Python compilation/indentation and nine regression tests pass. Build and validation pass for 63 routes, 68 HTML files and 6,128 local links. EPUB metadata uses the new title. All 36 manuscript bodies match the previous commit after excluding editorial title/version lines. Chrome desktop and 390 px mobile previews show readable titles/subtitles without horizontal overflow; language switching and new download targets were checked.

A read-only Codex review found one issue in promotion bookkeeping: the current X verification still described the initial 16-post schedule after two announcements had published. Resolved by preserving `initial_scheduling_verification` separately and recording the current 14 scheduled / 2 published state. Counts and draft/published distinctions were then asserted against individual post statuses. No unresolved review finding remains.

The two revised launch texts are local drafts, not replacement publications. Published-post deletion status is tracked in `promotion/x-launch.json`; the remaining 14 scheduled entries contain no old book title.

## Original declaration reading pages — 23 September 2026

The homepage's Simplified Chinese, Traditional Chinese and English declaration links now lead to `/original/zh-Hans/`, `/original/zh-Hant/` and `/original/en/` under the existing site base. Each page reads its original Markdown file and provides a link back to that file on GitHub. Serif typography, warm paper surfaces, a dark theme and a restrained reading column are confined to these pages.

Source preservation: all three SHA-256 hashes match the originals before this change. Tests compare rendered text and every source link, preserve the two lists of 3 and 16 items, and retain all 327 signature links in each Chinese version. The Chinese signatures use an expandable native disclosure; no signature section is invented for the English version. Original Markdown files and book manuscripts are unchanged.

Automated verification: all 13 regression tests pass; Ruff formatting and lint pass; mypy reports no issues in seven source files; Python compilation and Git whitespace checks pass. The build produces 66 content routes and validates 71 HTML files and all 6,161 local links, plus EPUB and sitemap XML. The generated source-hash metadata is valid JSON, and the updated GitHub Actions YAML parses with both source-path triggers present. Temporary quality tools remain outside the repository; no production dependency was added.

Browser verification in Chrome: all three declarations fit widths of 320, 768 and 1440 px with one page title, one current-language marker, two intact lists and no horizontal page overflow. Traditional Chinese and English were also visually checked at 390 px. Desktop light/dark and 320 px light/dark layouts were inspected. Language switching resets scroll, returning to the book reaches the homepage, the theme survives navigation and reload, keyboard Tab reaches the skip link and Enter focuses the main content, and expanding the Traditional Chinese signatures preserves 327 links without overflow. Source links point to their unchanged originals. Navigation and signature disclosure are native HTML and do not depend on JavaScript.

Accessibility adjustment: darkened muted text so the small language-navigation and return links meet a 4.5:1 contrast ratio against the surrounding paper background. Print colors also override the dark palette explicitly.

A read-only Codex review of the complete declaration-reader change found no actionable issues. No blocking quality findings remain. The update uses the existing GitHub Pages build and deployment workflow.
