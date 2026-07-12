# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DL Fantasy — a personal, dark-themed archive site (Django) for one author's fiction, philosophy,
and mythology writing, centered on a flagship story called "The God Valley". Content is
single-author (only Mr. Dex writes/publishes, via Django admin). **The original "no visitor
accounts" idea is cancelled** — the site now supports and will keep supporting real user accounts:
sign up, log in, log out, and a personal account page, with more account-driven features expected
to build on this (see the drawer's Favourite/Bookmarks/Reading List/News placeholders). See
**Visitor auth** below for how it's built. Full intent lives in `Project-Scope.md` — read it for the
"why", but see **Divergences from Project-Scope.md** below before trusting it for the current
page/nav structure, since the build has moved past it in a few places.

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

- **`users`** — custom `User(AbstractUser)` model, no extra fields on `User` itself, wired as
  `AUTH_USER_MODEL = 'users.User'` from the very first migration (so the later switch to real
  visitor accounts — see **Visitor auth** below — never needed a destructive user-table migration;
  don't revert to `django.contrib.auth.User`). The app also owns two auth-adjacent models,
  `LoginHistory` and `DailyVisit`, plus `signals.py` / `middleware.py` / `utils.py` /
  `context_processors.py` supporting visitor auth.
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
clock+account-icon+menu on one row. Because the DOM order (logo, then links, then the right-hand
group) doesn't match left-to-right column order, all three children need an explicit `grid-row: 1`
— without it, CSS grid's sparse auto-placement bumps out-of-order items onto a second row. There is
no search input in the navbar itself — see the **Search** divergence bullet below for where
site-wide search actually lives now.

### Visitor auth: real sessions layered onto `users` + `core`

Beyond the admin-only content-publishing surface, the site has real visitor authentication —
sign up, log in, log out, and a personal account page — all session-based via Django's built-in
auth. Routes live in `core/urls.py`/`core/views.py` (`signup`, `login_view`, `account`, plus
`django.contrib.auth`'s built-in `LogoutView`/`PasswordChangeView`/`PasswordChangeDoneView` wired
inline), matching the "core owns all views/URLs" convention above. Forms live in `core/forms.py`
(`SignupForm`, `StyledAuthenticationForm`, `StyledPasswordChangeForm`) rather than `users/forms.py`,
since `core` already reaches into other apps' models directly (`from upload.models import Content`).
`StyledPasswordChangeForm` subclasses Django's `SetPasswordForm`, not `PasswordChangeForm` — there
is deliberately no current-password check on `/account/password/` right now (removed at explicit
request; revisit once real account security is in scope).

`users/models.py` has two auth-adjacent models beyond `User`:
- **`LoginHistory`** — one row per successful login, populated via the `user_logged_in` signal
  (`users/signals.py`, connected in `users/apps.py`'s `ready()`). Admin-visible but not currently
  surfaced on any page.
- **`DailyVisit`** — one row per `(user, date)`, deduped so browsing many pages in one day only
  counts once. Populated by `users/middleware.py`'s `TrackDailyVisitMiddleware` (registered in
  `MIDDLEWARE`, after `AuthenticationMiddleware`). This — not `LoginHistory` — powers the "Visits
  (Last 30 Days)" figure and the pure-CSS bar chart on the account page: sessions persist
  indefinitely once logged in, so a raw login count wouldn't reflect actual site engagement the way
  a deduped daily-visit count does.

Profile photo is Gravatar-derived, not uploaded: `users/utils.py` hashes the account's email into a
gravatar.com URL, exposed site-wide via `users/context_processors.py`'s `avatar` context processor
(registered in `TEMPLATES.OPTIONS.context_processors`) so `base.html`'s navbar can render it on
every page without each view passing it manually. `LOGIN_URL` / `LOGIN_REDIRECT_URL` /
`LOGOUT_REDIRECT_URL` are set in `settings.py` (there were no defaults before this feature).

The navbar's profile-circle button (`base.html`) is conditional: an anonymous visitor sees a
generic person-icon SVG linking to `/login/`; a logged-in visitor sees their Gravatar image linking
to `/account/` (not a future "Profile" page — that's a separate, not-yet-built page). The side
drawer's Logout button is a real `POST` form (Django 5's `LogoutView` requires POST); the other
drawer items (Favourite, Bookmarks, Reading List, Downloads, News) are still static placeholders,
unconnected to any account data.

### Design system: token-based, gold-on-ink

All visual styling lives in one `static/css/style.css` (no frontend build step — plain CSS,
self-hosted `@font-face` fonts from `static/fonts/`). The palette/type pairing is a deliberate
choice, not a template default: near-black ink background (`--bg-primary #050505`) with a gold
accent (`--gold #d4af37`) evoking illuminated-manuscript/divine imagery that fits "The God Valley"'s
gods-and-power themes, paired with `'Cormorant Garamond'` (serif, headings/display, used sparingly)
and `'Inter'` (sans, body/UI, weights 300–700 self-hosted). Everything else is driven off `:root`
custom properties: a spacing scale (`--space-2xs` through `--space-3xl`), radius tokens
(`--radius-sm`/`--radius-md`), a shared easing curve (`--ease`), shadow tokens (`--shadow-card`,
`--shadow-lift`), and `--gutter` — a `clamp()`-based side padding used on `.navbar`/`.hero`/
`.archive`/`footer`/`.home-search` so content stays close to the viewport edge on wide screens
instead of an unbounded percentage-based gutter growing forever. Buttons/cards reuse
`.btn`/`.btn-outline`/`.archive-card` consistently across pages rather than one-off per-template
styles. The site respects `prefers-reduced-motion` (disables hero/card entrance animations and the
JS parallax effect without leaving content stuck at `opacity:0`) and has visible `:focus-visible`
states site-wide. Hero sections are written inline per-template (`<section class="hero">...`)
rather than via a shared include — an earlier `_hero.html` partial was deliberately deleted in
favor of consistency with the pages that never used it.

## Divergences from Project-Scope.md

The scope doc was the starting brief; the build has since deviated in ways later instructions
deliberately introduced. Trust the code over the doc on these points:

- **Nav/pages**: scope says `Home / Writings / God Valley / About` and explicitly says to drop
  Archive/Concepts from the old project's nav. Current nav is
  `Home / Writings / God Valley / Archive`, and Archive/Concepts/Collections all exist (Concepts
  and Collections are placeholders pending real content).
- **Writings sub-categories**: scope says Fiction / Essays / Poetry. Current `Content.Category` is
  Fiction / Philosophy / Mythology.
- **Search**: scope says no search feature at launch. Site-wide search is now live, posting to
  `/search/` (`core.views.search`, title-only match across all published content, both Writings and
  God Valley) — it lives as a static, centered search bar at the top of the homepage
  (`templates/home.html`'s `.home-search` section), not in the navbar; there is no search input in
  `.navbar` itself. `godvalley_chapters`'s own `?q=` chapter-title filter is unchanged and still
  separate — a narrower, page-scoped search that coexists with the site-wide one rather than being
  replaced by it.
- **Visitor accounts**: scope (and this doc's original framing) said single-author with no visitor
  accounts and Django admin as the only authenticated surface. **That idea is cancelled, not just
  diverged from** — user accounts are now a permanent, intentional part of the site, not a
  workaround or a temporary exception. The site has real visitor sign-up/login/logout/account pages
  — see **Visitor auth** above. Admin remains the only surface for *publishing* content; it's no
  longer the only *authenticated* surface, and won't go back to being one.
- **Database**: scope says MySQL, and the project now runs on MySQL (`dlfantasy/settings.py`
  `DATABASES`), reading `DB_NAME`/`DB_USER`/`DB_PASSWORD`/`DB_HOST`/`DB_PORT` from a gitignored
  `.env` via `python-dotenv` (`load_dotenv(..., override=True)` — deliberately overrides any
  same-named variable already set in the OS environment, since a stray system-level `DB_PASSWORD`
  has shadowed the project's `.env` value before). There are no defaults on any of these
  `os.environ[...]` lookups, so the app crashes on startup with a `KeyError` if `.env` isn't
  populated. A leftover `db.sqlite3` file sits at the repo root from before this switch — it is
  gitignored and no longer read by `settings.py`; safe to delete manually, not done automatically
  here since it wasn't asked for.

## Planned direction

- **Form validation → Zod.** All current forms (`core/forms.py`'s `SignupForm`,
  `StyledAuthenticationForm`, `StyledPasswordChangeForm`, plus the `?q=` search inputs) are
  server-side Django `forms.Form`/`forms.ModelForm` validation only, no client-side validation
  layer. The intended direction is to move form validation to Zod. Note this is currently
  unreconciled with **"Commands"** above stating there's no frontend build step — Zod is a
  TypeScript/JS schema library with zero wiring into this project today, so adopting it means
  deciding how it's delivered (a vendored/CDN `<script>` kept build-step-free, vs. introducing an
  actual JS build step) as part of that migration, not an assumption to carry over silently.
