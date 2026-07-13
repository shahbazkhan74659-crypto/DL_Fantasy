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
  `LoginHistory` and `VisitSession`, plus `signals.py` / `middleware.py` / `utils.py` /
  `context_processors.py` supporting visitor auth.
- **`upload`** — owns the `Content` model, a central table for *all* long-form content: Fiction,
  Philosophy, Mythology, and God Valley chapters, distinguished by a `category` `TextChoices` field.
  God Valley intentionally lives in this shared table for now; Project-Scope.md calls for splitting
  it into its own dedicated model later once volume justifies it. Key fields: `chapter_number`
  (nullable — only meaningful for `category=godvalley`, drives chapter ordering and prev/next nav)
  and a `UniqueConstraint` on `(category, slug)` rather than a global-unique slug, since the same
  slug could otherwise collide across categories. `upload` also owns a separate, deliberately
  distinct `News` model (short dispatches — no chapters, no `category`, just
  `title`/`tag`/`body`/`created_at`) — see **News** below.
- **`core`** — all views and URLs; holds no models. `core/urls.py` is included from the project
  root `dlfantasy/urls.py` at `''`.

### News: `upload.News`, created/edited via a modal, not Django admin

The News page (`/news/`) is real content management, not another static page — an admin can add a
new dispatch through a "+ New" button (visible only when `user.is_staff`) that pops open a modal
(`templates/news.html`, `static/js/news.js`) asking for **Title**, **Content**, and a **Tag**
(exactly three choices: `Announcement` / `News` / `Update` — `upload.models.News.Tag`). The date is
never user-entered: `created_at` is `auto_now_add`. Submitting POSTs to `core.views.create_news`
(`core/forms.py`'s `NewsForm`), which — like `edit_user`/`delete_user` on the Users page — is gated
by `if not request.user.is_staff: raise Http404` regardless of whether the button is visible,
so hitting the URL directly as a non-admin 404s rather than 403s (matches the rest of the
admin-only surface on this site). `News.slug` is generated server-side in `News.save()`, not via
Django admin's `prepopulated_fields` JS helper — the modal isn't Django admin, so nothing else
would fill it in. `News` *is* also registered in Django admin (`upload/admin.py`) for direct
editing/deletion, same as `Content`. `news_detail.html` reuses the `.hero`/`.archive`/
`.chapter-content` pattern from `writings_detail.html`, but with a `hero-compact` modifier class
(and a `.hero-compact + .archive` CSS override) since the full 90vh splash hero looks wrong on a
short dispatch instead of a long chapter.

Each News card also carries a three-dot menu (Edit/Delete, `user.is_staff`-only) built from the
**reusable card menu module** below — Edit reopens the same modal as "+ New" (pre-filled via the
button's `data-*` attributes, form `action` swapped to `core.views.edit_news`), and Delete is a
real `<form method="post">` to `core.views.delete_news` with a JS `confirm()` guard. Both views
follow the same `is_staff` + `Http404` gate as `create_news`. Since each card's whole body is
clickable (see **stretched-link** below), the card itself is no longer an `<a>` — the title is now
`<h3><a class="stretched-link">`, letting the three-dot menu sit as an independently-clickable
sibling instead of an invalid nested interactive element inside an anchor.

### Reusable card menu: `templates/_card_menu.html` + `static/js/card-menu.js`

A three-dot dropdown menu, built once and meant to be dropped onto *any* card, not just News.
Usage: `{% include '_card_menu.html' with actions=item.menu_actions %}`, where `menu_actions` is a
list of dicts built server-side (see `core.views.news`) shaped as one of:
`{'type': 'link', 'label', 'url'}`, `{'type': 'edit-modal', 'label', 'url', 'trigger_class',
'data': {...}}` (data becomes `data-*` attrs for a page's own JS to read on click — genuinely
generic, not News-specific), or `{'type': 'delete', 'label', 'url', 'confirm'}`. The open/close/
outside-click/Escape behavior lives in `card-menu.js` as a single **delegated** listener on
`document` (registered once, site-wide, via `base.html` — not per-page `extra_js`), so it already
works for any future `.card-menu` a page adds, including ones rendered after page load, with zero
additional JS wiring — only the page-specific *actions* (like News's edit-modal trigger) need their
own small handler. The delete confirmation (`window.confirm()` on `[data-confirm]`) is handled
generically inside `card-menu.js` too, not duplicated per feature.

### Stretched-link: whole-card click target without nesting interactive elements

`.stretched-link` (on the title `<a>`) expands via `::after{position:absolute;inset:0}` to cover
its nearest positioned ancestor (the `.archive-card`, already `position:relative`), making the
entire card clickable through one small visible link — this is what lets a card carry both a
full-card click-through *and* an independently-clickable `.card-menu` on top of it (`z-index:2` vs.
the stretched overlay's `z-index:1`) without illegally nesting a `<button>`/`<form>` inside an
`<a>`. `.stretched-link` itself resets `color:inherit;text-decoration:none` — without that, the
inner `<a>` shows the browser's default blue/underlined link style instead of inheriting
`.archive-card h3`'s gold color, since the anchor is now nested inside the heading rather than
wrapping it.

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

The public login form (`/login/`) authenticates by **email**, not username, even though `User`'s
`USERNAME_FIELD` is still `username` (unchanged, so `createsuperuser`/admin login are unaffected).
`StyledAuthenticationForm` keeps the form field internally named `username` — required, since
Django's `AuthenticationForm.clean()` always calls `authenticate(username=<value>, ...)` regardless
of the field's label — and just relabels it "Email" with an `EmailInput` widget; the actual email
lookup happens in `users/backends.py`'s `EmailBackend.authenticate()`, which resolves the typed
value via `email__iexact` instead of the default username lookup. `AUTHENTICATION_BACKENDS`
(`settings.py`) lists `EmailBackend` before Django's own `ModelBackend` rather than replacing it, so
Django admin's separate username-based login form keeps working through the same setting. There is
no DB-level uniqueness constraint on `email` (MySQL doesn't support the partial/conditional unique
index that would be needed to allow multiple blank emails while still forbidding duplicate real
ones) — `SignupForm.clean_email()` enforces uniqueness at the application level instead;
`EmailBackend` treats an unexpected duplicate as a failed login (via `MultipleObjectsReturned`)
rather than guessing which account was meant.

`users/models.py` has two auth-adjacent models beyond `User`:
- **`LoginHistory`** — one row per successful login, populated via the `user_logged_in` signal
  (`users/signals.py`, connected in `users/apps.py`'s `ready()`). Admin-visible but not currently
  surfaced on any page.
- **`VisitSession`** — one row per distinct *visit* (a burst of activity), not per day. Populated
  by `users/middleware.py`'s `TrackVisitSessionsMiddleware` (registered in `MIDDLEWARE`, after
  `AuthenticationMiddleware`): each authenticated request either starts a new row (`started_at` =
  `last_seen_at` = now) or bumps an existing row's `last_seen_at`, based on a 30-minute inactivity
  gap (`SESSION_GAP`) tracked in the Django session, with an explicit calendar-day-rollover check so
  a visit spanning midnight doesn't get misattributed. Visit count and time-on-site are both derived
  at query time — `core.views.account` groups by `date` and computes `Count('id')` /
  `Sum(last_seen_at - started_at)` — rather than stored as a running total, so there's no stale
  aggregate to drift from reality. This — not `LoginHistory` — powers the "Visits (Last 30 Days)"
  and "Time Spent (Last 30 Days)" figures and the pure-CSS bar chart on the account page: sessions
  persist indefinitely once logged in, so a raw login count wouldn't reflect actual site engagement
  the way per-visit tracking does.

Profile photo prefers a real Google account photo, falling back to Gravatar, not uploaded:
`users/context_processors.py`'s `avatar` context processor (registered in
`TEMPLATES.OPTIONS.context_processors`) exposes a single `avatar_url` site-wide — `User.
google_picture_url` if the account has signed in with Google at least once, else a Gravatar URL
hashed from the account's email (`users/utils.py`). This two-tier fallback exists because Gravatar
and a Google/Gmail account photo are unrelated services — hashing an email only looks up a Gravatar
profile, which most Gmail addresses don't have, so Gravatar alone silently showed a generic
mystery-person icon instead of the photo people actually expected. `LOGIN_URL` /
`LOGIN_REDIRECT_URL` / `LOGOUT_REDIRECT_URL` are set in `settings.py` (there were no defaults
before the visitor-auth feature).

### "Sign in with Google": `core/google_oauth.py`

A hand-rolled (not django-allauth) OAuth2 client, deliberately minimal since the only thing it's
for is pulling a verified email/name/photo — pulling in a full social-auth framework for that would
be a lot of surface for one provider. `google_login`/`google_callback` (`core/views.py`, wired in
`core/urls.py`) drive the flow: `google_login` redirects to Google's consent screen with a random
per-session `state` (CSRF protection, single-use, popped from the session on callback);
`google_callback` exchanges the returned `code` for tokens via `requests`, then verifies the
`id_token`'s signature/issuer/audience/expiry with `google.oauth2.id_token.verify_oauth2_token`
(the `google-auth` package) rather than decoding the JWT by hand — hand-rolled JWT verification is
exactly the kind of thing that quietly becomes a security hole. Matching an incoming Google
identity to a local `User` prefers `User.google_sub` (Google's stable per-account ID — the actual
identity, since emails can change) and falls back to `email__iexact` to link an existing
password-based account the first time someone uses Google on it; if neither matches, a new `User`
is created with `set_unusable_password()` (Google-only accounts can't log in via the password form)
and a username auto-derived from the email's local part, deduped against existing usernames.

The whole feature is optional and self-hiding: `GOOGLE_OAUTH_CLIENT_ID` / `GOOGLE_OAUTH_CLIENT_SECRET`
are read via `os.environ.get(...)` with an empty-string default (unlike the mandatory `DB_*` vars
above, which deliberately crash on startup if unset) — `google_oauth.is_configured()` gates both
views (404 if unset) and the "Continue with Google" button on `login.html`/`signup.html` (hidden
via `google_oauth_enabled` in each view's context), so a checkout of this repo without Google
credentials in `.env` runs exactly as it did before this feature existed. Getting real credentials
requires a free Google Cloud Console project + OAuth Client ID (no billing needed for the
`openid`/`email`/`profile` scopes used here) — that step has to be done by whoever owns the Google
Cloud project, not from inside this codebase.

The navbar's profile-circle button (`base.html`) is conditional: an anonymous visitor sees a
generic person-icon SVG linking to `/login/`; a logged-in visitor sees their `avatar_url` image
linking to `/account/` — deliberately still `/account/`, not `/profile/` (see below), even though
both now exist; `/account/` remains the primary post-login landing spot. The side drawer's Logout
button is a real `POST` form (Django 5's `LogoutView` requires POST); the drawer's own Profile item
links to `/profile/`; the remaining drawer items (Favourite, Bookmarks, Reading List, Downloads,
News) are still static placeholders, unconnected to any account data.

### Profile (`/profile/`) vs. Account (`/account/`) — two different pages, on purpose

`/account/` (`core.views.account`) is the stats dashboard: visit count/time-on-site, the 30-day
bar chart, a link to change password. `/profile/` (`core.views.profile`, `templates/profile.html`)
is the identity page, built to a specific two-column brief: a fixed-width left column (avatar,
username, email, an Admin/User `.user-badge` — reusing the same badge classes as the `/users/`
table — and an "Edit Profile" button) separated by a `.profile-divider` from a right column headed
"Reading History". Each page links to the other (`.account-actions` on `/account/`, and `/profile/`
has no stats of its own) so neither is a dead end.

"Edit Profile" opens a modal (`static/js/profile.js`) wrapping the same `ProfileForm` used before —
deliberately narrower than `UserEditForm` (the admin-facing one on `/users/`): no `is_active`
field, since deactivating your own account through a plain form isn't a lever a self-service page
should expose. Unlike the JS-driven modals elsewhere (Users, News), this one doesn't need JS to
open on a failed submit: `profile.html` renders the modal with `is-open` server-side
(`{% if form.errors %}`) so validation errors are never hidden behind a closed modal on page
reload — the *closing* is JS, but the *first open on error* isn't.

Reading History is powered by `upload.models.ReadingHistory` — one row per `(user, content)`,
deduped the same way `VisitSession`/`google_sub` linking are (a real unique constraint, not an
app-level check), with `viewed_at` as `auto_now` (not `auto_now_add`) so re-reading something
bumps it back to the top of the list instead of leaving a stale timestamp. It's recorded from
`core.views._record_reading_history`, called from both `writings_detail` and `godvalley_detail`
for authenticated visitors only (anonymous reading isn't tracked — there's no account to attach it
to). `/profile/` shows the 10 most recent; zero rows renders "No History Recorded." instead of an
empty list.

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

## Client-side validation: Zod, vendored, no build step

`login.html` and `signup.html` now have client-side validation via Zod, layered on top of (not
replacing) the existing server-side Django `forms.Form`/`forms.ModelForm` validation in
`core/forms.py` — Django remains the source of truth; the client-side layer is purely a fast-fail
UX improvement. Delivery keeps the "no frontend build step" constraint from **Commands** above:
Zod's ESM bundle is vendored at `static/vendor/zod.js` (fetched from jsdelivr's `+esm` build,
external sourcemap comment stripped) rather than loaded from a CDN at runtime — consistent with how
this project already self-hosts fonts instead of using a CDN. `static/js/auth-forms.js` is a
`type="module"` script, loaded only on the two auth pages via `base.html`'s `{% block extra_js %}`
(not site-wide), that defines a schema per form (`login`, `signup` — keyed off the form's
`data-zod` attribute) mirroring the server-side rules (username charset/length, email format,
`AUTH_PASSWORD_VALIDATORS`' min-length-8 and not-all-numeric checks, password confirmation match).
On submit it writes per-field messages into each field's `[data-field-error="<name>"]` element and
calls `event.preventDefault()` only when invalid; a passing client-side check lets the native POST
through to Django unmodified, so the flow still works end-to-end with JS disabled — Django just
does all the validating in that case, same as before. `StyledPasswordChangeForm` and the `?q=`
search inputs are **not** wired to Zod yet — this covers login/signup only so far.

Both auth pages also moved into a centered `.auth-card` (see `static/css/style.css`'s "AUTH CARD"
block) — a boxed, vertically-centered card with a thin gold top hairline and ambient
`--gold-glow` bloom (a previously-declared-but-unused token), rather than the old plain
left-aligned column. `account.html` intentionally still uses the older plain `.auth-container`
layout, not `.auth-card` — its content (stats grid, activity chart) doesn't fit a narrow centered
card the way a short credentials form does.
