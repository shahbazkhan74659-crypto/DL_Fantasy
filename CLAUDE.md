# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DL Fantasy — a personal, dark-themed archive site (Django) for one author's fiction, philosophy,
and mythology writing, centered on a flagship story called "The God Valley". Single-author,
no visitor accounts; Django admin is the only authenticated surface. Full intent lives in
`Project-Scope.md` — read it for the "why", but see **Divergences from Project-Scope.md** below
before trusting it for the current page/nav structure, since the build has moved past it in a few
places.

## Commands

Windows venv, activated via `venv\Scripts\activate` (PowerShell/cmd) — all commands below assume
the venv's Python (`venv\Scripts\python` / `venv/Scripts/python` if not activated).

```
pip install -r requirements.txt     # Django, mysqlclient, python-dotenv
python manage.py runserver          # dev server at http://127.0.0.1:8000/
python manage.py makemigrations     # add [app_label] to scope to one app, e.g. `upload`
python manage.py migrate
python manage.py createsuperuser    # only way to get an admin login — always run interactively
python manage.py shell              # ORM access, e.g. `from upload.models import Content`
python manage.py check              # settings/model sanity check, no DB needed
python manage.py test               # core/tests.py covers all 11 views; `test <app>.<TestCase>.<method>` to scope one
```

`requirements.txt` pins `Django`, `mysqlclient`, and `python-dotenv`. No frontend build step;
templates and `static/` are served directly.

## Architecture

Three apps, one Django project (`dlfantasy/`):

- **`users`** — custom `User(AbstractUser)` model with no extra fields yet, wired as
  `AUTH_USER_MODEL = 'users.User'` from the very first migration. It exists purely so a future
  switch to non-admin accounts doesn't require a destructive user-table migration; don't revert to
  `django.contrib.auth.User`.
- **`upload`** — owns the single `Content` model, a central table for *all* long-form content:
  Fiction, Philosophy, Mythology, and God Valley chapters, distinguished by a `category`
  `TextChoices` field. God Valley intentionally lives in this shared table for now; Project-Scope.md
  calls for splitting it into its own dedicated model later once volume justifies it. Key fields:
  `chapter_number` (nullable — only meaningful for `category=godvalley`, drives chapter ordering
  and prev/next nav) and a `UniqueConstraint` on `(category, slug)` rather than a global-unique slug,
  since the same slug could otherwise collide across categories.
- **`core`** — all views and URLs; holds no models. `core/urls.py` is included from the project
  root `dlfantasy/urls.py` at `''`.

All templates live in one top-level `templates/` directory (`TEMPLATES.DIRS`), not per-app —
none of the three apps use Django's app-level `templates/<app>/` convention.

### Writings: one generic view pair drives three categories

`core/views.py` defines `WRITINGS_CATEGORIES = (FICTION, PHILOSOPHY, MYTHOLOGY)` and reuses
`writings_category_list` / `writings_detail` for all three — the `category` URL kwarg is matched
straight against `Content.Category` values, which double as URL path segments
(`/writings/<category>/`). Adding a fourth Writings sub-category means updating
`Content.Category`, this tuple, and the nav/`writings.html` cards — nowhere else.

`writings_category_list` and `godvalley_chapters` are paginated (`core/views.py`'s `_paginate`
helper, `PAGE_SIZE = 12`, rendered via `templates/_pagination.html`) — any new list view should use
the same helper rather than passing a raw queryset straight to the template.

### God Valley is split into three pages, not one

Unlike Writings, God Valley has dedicated views because it needed an intro/story page, not just a
list+detail:

- `godvalley_list` (`/godvalley/`) — static hero + lore/story blurb, no DB query. This is the page
  linked from the navbar and from the Archive index.
- `godvalley_chapters` (`/godvalley/chapters/`) — the actual chapter grid, with `?q=` title search
  (`Content.objects.filter(title__icontains=...)`). This is the only real search on the site.
- `godvalley_detail` (`/godvalley/<slug>/`) — chapter body + prev/next, computed via two indexed
  `chapter_number__lt`/`__gt` queries with `.only(...)` (not a full-table scan; avoids loading every
  chapter's `body` just to find neighbors).

### Archive / Concepts / Collections / About

The navbar's fourth link is **Archive** (`/archive/`), not About. Archive is a directory-index page
(styled with `.archive-list-item` rows) linking out to: God Valley (`godvalley_list`), Concepts,
Collections, and About. `concepts` and `collections` are currently heading-only placeholder pages
with no model behind them. `about` holds the actual "who I am / what this site is" bio content,
and refers to the author in-character as **Mr. Dex** (site name "DL" = "Dex Library").

### Syndication / SEO: `core/feeds.py` and `core/sitemaps.py`

`LatestContentFeed` (`core/feeds.py`, `django.contrib.syndication`) serves the last 20 published
`Content` rows, newest first, at `/feed/`; `base.html` links it via
`<link rel="alternate" type="application/rss+xml">` for reader auto-discovery. `core/sitemaps.py`
registers two `Sitemap` classes at `/sitemap.xml` (wired in `dlfantasy/urls.py`, requires
`'django.contrib.sitemaps'` in `INSTALLED_APPS`): `ContentSitemap` (all published `Content`) and
`StaticViewSitemap` (the static pages only — home/writings/godvalley_list/godvalley_chapters/
archive/about). `concepts`/`collections` are deliberately excluded from both, since they're
placeholder pages with no real content yet.

### Navbar layout is a 3-column CSS grid, not flex

`.navbar` uses `grid-template-columns: 1fr auto 1fr` to get nav-links / centered logo /
search+clock on one row. Because the DOM order (logo, then links, then search+clock) doesn't match
left-to-right column order, all three children need an explicit `grid-row: 1` — without it, CSS
grid's sparse auto-placement bumps out-of-order items onto a second row. The navbar search input
posts to `/search/` (site-wide, title-only) — see the **Search** divergence bullet below for how
this relates to the separate, page-scoped `?q=` search on `/godvalley/chapters/`.

## Divergences from Project-Scope.md

The scope doc was the starting brief; the build has since deviated in ways later instructions
deliberately introduced. Trust the code over the doc on these points:

- **Nav/pages**: scope says `Home / Writings / God Valley / About` and explicitly says to drop
  Archive/Concepts from the old project's nav. Current nav is
  `Home / Writings / God Valley / Archive`, and Archive/Concepts/Collections all exist (Concepts
  and Collections are placeholders pending real content).
- **Writings sub-categories**: scope says Fiction / Essays / Poetry. Current `Content.Category` is
  Fiction / Philosophy / Mythology.
- **Search**: scope says no search feature at launch. The navbar search box is now live, posting to
  `/search/` (`core.views.search`, title-only match across all published content, both Writings and
  God Valley). `godvalley_chapters`'s own `?q=` chapter-title filter is unchanged and still separate
  — a narrower, page-scoped search that coexists with the site-wide one rather than being replaced
  by it.
- **Database**: scope says MySQL, and the project now runs on MySQL (`dlfantasy/settings.py`
  `DATABASES`), reading `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` from a gitignored
  `.env` via `python-dotenv` (`load_dotenv(..., override=True)` — deliberately overrides any
  same-named variable already set in the OS environment, since a stray system-level `DB_PASSWORD`
  has shadowed the project's `.env` value before). There are no defaults on any of these
  `os.environ[...]` lookups, so the app crashes on startup with a `KeyError` if `.env` isn't
  populated. A leftover `db.sqlite3` file sits at the repo root from before this switch — it is
  gitignored and no longer read by `settings.py`; safe to delete manually, not done automatically
  here since it wasn't asked for.
