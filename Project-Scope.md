# DL Fantasy — Project Scope

> Working defaults below — flag anything to change as we build.

## Idea

A personal website to share fictional stories, philosophies, and knowledge —
centered on my main story, **The God Valley**. Dark aesthetic theme.

## Vision

A quiet, dark-themed personal archive rather than a blog-with-comments or a
social platform. One author (me), managed through Django admin. Visitors
read; they don't sign up, post, or interact. The site should feel like
flipping through a private notebook that's been made public — moody,
minimal, text-first.

## Site Structure

Four pages, kept deliberately small in scope:

### `Home/`
- Hero section: site name, tagline, dark aesthetic.
- A rotating/recent selection of entries pulled from Writings and God Valley
  (fixes the "always empty" bug the old project had — this must actually
  pass context and use real field names this time).
- Nav into the other three pages.

### `Writings/`
Landing page linking into sub-categories, matching "fictional stories, my
philosophies, my knowledge":
- **Fiction** — short stories, one-offs (not God Valley — that has its own page).
- **Essays** — philosophy, ideas, worldview pieces.
- **Poetry**
- Each sub-category is a list page (title + excerpt + date) → detail page
  (full content).

### `God Valley/`
Treated as its own first-class thing, not just another Writings category,
since it's called out as the main story:
- Chapter list page — ordered by chapter number, searchable/filterable by title.
- Chapter detail page — chapter number, title, full content, prev/next
  chapter navigation.

### `About/`
- Static page: who I am, what this site is, how it's organized.
- No database model needed — a template is enough.


## Access / Accounts

No visitor accounts, no login/signup. The entire site is public — anyone can
read every page. Admin login (Django's built-in `/admin`) is the only
authenticated surface, and it's for me only.

## Design

- Reuse `static/` (fonts, `style.css`, `main.js`) and `base.html` from the
  old `dlfantasy` project as the starting point for layout/nav/footer.
- Dark aesthetic: current fonts (Cormorant Garamond for display, Inter for
  body) and dark color palette carry over unless we decide to redesign.
- Simplified nav: Home / Writings / God Valley / About (drop Concepts, Dex,
  Archive, Login/Signup links from the old nav).

## Explicit Non-Goals (for now)

- No user accounts, comments, likes, or social features.
- No search feature at launch (the old project's search was broken/partial —
  revisit only if the content volume grows enough to need it).
- No tagging/filtering system beyond category and chapter order.
- No "Concepts" (power systems / cosmology / civilizations) or "Dex"
  (philosophy/religion/science) sections carried over from the old project —
  fold anything worth keeping into Writings or God Valley chapters instead.

## Tech Stack

- Django (matching the old project's version — Django 5.x installed locally).
- MySQL for the database (fine at this scale; no reason to add Postgres yet).
- Plain Django templates + the existing `static/` assets — no frontend
  framework, no build step.

## Open Questions (revisit as needed)

- Should God Valley chapters support drafts/unpublished chapters visible
  only via admin preview, or is `is_published` binary good enough?
- Does "knowledge" (from the original idea) need its own Writings
  sub-category, or does it live inside Essays?
- Any need for an RSS feed or sitemap for discoverability?
