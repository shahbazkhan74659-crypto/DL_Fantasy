# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

DL Fantasy — a personal, dark-themed archive site (Django) for one author's fiction, philosophy,
and mythology writing, centered on a flagship story called "The God Valley". Content is
single-author (only Mr. Dex writes/publishes — via the admin-only **Upload page** below day-to-day,
or Django admin directly). **The original "no visitor
accounts" idea is cancelled** — the site now supports and will keep supporting real user accounts:
sign up, log in, log out, and a personal account page, with more account-driven features expected
to build on this. Favourite, Reading List, and Downloads are now real, account-backed features (see
**Favourites and Reading List** and **Downloads: on-demand PDF export** below); Bookmarks in the
side drawer is gated `{% if user.is_staff %}` — visible to Mr. Dex (admin) only, hidden from regular
visitors — pending a concrete design for a real visitor-facing version. See the end of
**Visitor auth** below for the candidate directions considered. See **Visitor auth** below for how
visitor accounts are built.
Full intent lives in `Project-Scope.md` — read it for the "why", but see **Divergences from
Project-Scope.md** below before trusting it for the current page/nav structure, since the build has
moved past it in a few places.

## Commands

Windows venv, activated via `venv\Scripts\activate` (PowerShell/cmd) — all commands below assume
the venv's Python (`venv\Scripts\python` / `venv/Scripts/python` if not activated).

```
pip install -r requirements.txt     # Django, mysqlclient, python-dotenv, google-auth, requests, reportlab
python manage.py runserver          # dev server at http://127.0.0.1:8000/
python manage.py makemigrations     # add [app_label] to scope to one app, e.g. `upload`
python manage.py migrate
python manage.py createsuperuser    # only way to get an admin login — always run interactively
python manage.py shell              # ORM access, e.g. `from upload.models import Content`
python manage.py check              # settings/model sanity check, no DB needed
python manage.py test               # core/tests.py covers all 11 views; `test <app>.<TestCase>.<method>` to scope one
```

`requirements.txt` pins `Django`, `mysqlclient`, `python-dotenv`, `google-auth` + `requests` (Google
OAuth — see **"Sign in with Google"** below), and `reportlab` (PDF export — see **Downloads: on-
demand PDF export** below; pulls in `pillow` transitively, not pinned directly). No frontend build
step; templates and `static/` are served directly.

## Architecture

Three apps, one Django project (`dlfantasy/`):

- **`users`** — custom `User(AbstractUser)` model, no extra fields on `User` itself, wired as
  `AUTH_USER_MODEL = 'users.User'` from the very first migration (so the later switch to real
  visitor accounts — see **Visitor auth** below — never needed a destructive user-table migration;
  don't revert to `django.contrib.auth.User`). The app also owns two auth-adjacent models,
  `LoginHistory` and `VisitSession`, plus `signals.py` / `middleware.py` / `utils.py` /
  `context_processors.py` supporting visitor auth.
- **`upload`** — owns the `Content` model, a central table for *all* long-form content: Fiction,
  Philosophy, Mythology, and God Valley chapters, distinguished by a `category` `TextChoices` field
  (this top-level 4-way split is a fixed, intentionally-hardcoded set — see **Upload page** below for
  why, and don't confuse it with `Subcategory`, which is deliberately *not* hardcoded). God Valley
  intentionally lives in this shared table for now; Project-Scope.md calls for splitting it into its
  own dedicated model later once volume justifies it. Key fields: `chapter_number` (nullable — used
  for God Valley and Fiction chapter ordering; blank for Philosophy/Mythology, which aren't chaptered)
  and a `UniqueConstraint` on `(category, slug)` rather than a global-unique slug, since the same
  slug could otherwise collide across categories. `Content.save()` auto-generates `slug` from `title`
  when blank (same dedupe-loop pattern as `News.save()` below) — needed because the Upload forms
  (see **Upload page** below) don't expose a slug field; Django admin's `prepopulated_fields` JS
  still fills it client-side first, so admin behavior is unchanged. `upload` also owns `Subcategory`
  (see **Upload page** below) and a separate, deliberately distinct `News` model (short dispatches —
  no chapters, no `category`, just `title`/`tag`/`body`/`created_at`) — see **News** below. As of
  the **Upload page** feature, `upload` also owns its own `views.py`/`urls.py`/`forms.py` — a
  deliberate, called-out divergence from `core`'s "owns all views/URLs" convention below, scoped to
  just that one feature.
- **`core`** — all views and URLs *except* the Upload page (see above); holds no models.
  `core/urls.py` is included from the project root `dlfantasy/urls.py` at `''`.

### Upload page (`/upload/`): admin-only content creation, owned by the `upload` app

A dedicated in-site content-creation surface — not Django admin — living entirely in the `upload`
app (`upload/views.py`, `upload/urls.py`, `upload/forms.py`, included from `dlfantasy/urls.py` at
`/upload/`). `/upload/` is a hub with four cards (God Valley / Fiction / Philosophy / Mythology,
`upload.views.CARDS`), each opening a dedicated big form:
`upload_godvalley`/`upload_fiction`/`upload_philosophy`/`upload_mythology`. Every view is gated
`@login_required` + `if not request.user.is_staff: raise Http404` (same pattern as
`core.views.create_news`/`users_list` — anonymous visitors get redirected to login by
`login_required`, logged-in non-staff visitors get a 404, not a 403). On successful submit, the view
sets `category`/`author`/`is_published` itself (not exposed on any form) and redirects back to the
*same* upload sub-page rather than the new content's public page, since repeated chapter entry is
the expected workflow, not one-and-done.

`/upload/`'s four cards are a bespoke design, not the generic `_archive_card.html` include used
elsewhere — `upload.views.CARDS` centralizes each category's copy (`eyebrow`, `description`,
singular/plural noun) and an `icon` slug that `upload_hub.html` matches against an `{% if/elif %}`
chain to inline one hand-drawn SVG sigil per category (a radiant halo for The God Valley, a quill
for Fiction, a Doric column for Philosophy, an ouroboros ring for Mythology) — matching the site's
existing thin-stroke icon language rather than a stock photo, since this is an admin-only tool page,
not visitor-facing content. `upload_hub` computes each category's live item count in one aggregated
query (`Content.objects.values_list('category').annotate(...)`) rather than one query per card, and
picks the correct singular/plural noun in Python (`noun_singular`/`noun_plural` on each `CARDS`
entry) before handing the template a single `noun` string — needed because Django's `pluralize`
filter can't handle irregular plurals like story/stories. Each card's eyebrow tag reads "Flagship"
for The God Valley and "Writings" for the other three, mirroring the site's real content taxonomy
(God Valley is a standalone top-level story; Fiction/Philosophy/Mythology are the three Writings
sub-categories) rather than being decorative.

**`Subcategory`** (`upload.models.Subcategory`) is the piece that's actually meant to be
admin-extensible with zero code changes: which Fiction *story* a chapter belongs to, which
Philosophy *topic*, or which Mythology *tradition* — `parent_category` (one of Fiction/Philosophy/
Mythology; God Valley never uses it, it has exactly one implicit story) + `name`/`slug`, unique per
`(parent_category, slug)`. `Content.subcategory` is a nullable `FK(Subcategory, on_delete=PROTECT)`
— `PROTECT` is deliberate (not `CASCADE`), so a `Subcategory` can never be deleted while `Content`
still references it. Each of the three Subcategory-driven upload forms
(`upload.forms.SubcategoryUploadForm` and its Fiction/Philosophy/Mythology subclasses) lets the admin
either pick an existing `Subcategory` from a dropdown *or* type a brand-new one directly into a
`new_subcategory_name` field — `clean()` does a `get_or_create` on that name (slugified) under the
form's fixed `parent_category` — so a new story/topic/tradition never requires touching Django admin
or writing code, which is the whole point of the model existing. `Subcategory` is also registered in
Django admin (`upload/admin.py`) for direct editing, same as `Content`/`News`.

This replaced an earlier, narrower `Content.PhilosophyTopic` `TextChoices` field (hardcoded to just
Epistemology/Political Philosophy) — that field's two enum values became the first two `Subcategory`
rows via a data migration (`upload/migrations/0014_migrate_philosophy_topic.py`) before the old field
was dropped, so no existing classification was lost in the switch. The Philosophy category-filter bar
on `/writings/philosophy/` (`templates/writings_list.html`'s `.topic-filter`) now reads generically
off `Subcategory` — `core.views.writings_category_list` filters `?topic=<slug>` against
`Subcategory.objects.filter(parent_category=category)` — so the same filter bar mechanism works for
any category that ends up with subcategories, not just Philosophy, without further code changes.

### Editing and deleting existing content

Each upload sub-page's "Already Uploaded" list (`templates/upload_form.html`) carries an edit and a
delete icon per row (`.upload-existing-actions`), both admin-only. Editing opens a full, separate,
centered page — `/upload/edit/<pk>/` (`upload.views.edit_content`, `templates/upload_edit.html`) —
not an in-place modal; an AJAX modal-in-the-page approach was built and then deliberately reverted
in favor of a real page, so this is a considered choice, not an oversight. `upload_edit.html` reuses
the `.auth-page`/`.auth-card` centered-card layout already established for login/signup (with a
wider `.auth-card-wide` modifier, since a chapter body textarea needs more than the login form's
420px), and shows a `.meta` line below the heading with the item's title, chapter number (if any),
category, and upload date — the same `.meta` convention `writings_detail.html` uses below its own
`<h1>`. Saving redirects back to the category's upload page (`url_name`, resolved via
`{% url url_name %}` off a context variable) rather than the edited item's public page, matching the
create flow's "return to the workspace" convention above.

`delete_content` (`upload/views.py`) mirrors `core.views.delete_news`'s gate exactly — staff-only,
POST-only (`if not request.user.is_staff or request.method != 'POST': raise Http404`) — and
redirects back to the item's own category page with a success message. The delete icon is a real
`<form method="post">` (works with JS disabled) guarded by `data-confirm`, handled by the site-wide
confirm modal (see **Site-wide confirm modal** below) rather than a raw link, so a staff member can
never delete a chapter with a stray click. In the existing-items list, the category/subcategory tag
now trails the title (`Ch. N — Title` then the tag) rather than leading it — `.upload-existing-tag`'s
spacing was flipped from `margin-right` to `margin-left` to match.

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
real `<form method="post">` to `core.views.delete_news` guarded by the site-wide confirm modal (see
**Site-wide confirm modal** below). Both views
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
own small handler. The delete confirmation on `[data-confirm]` is handled generically inside
`card-menu.js` too, not duplicated per feature — see **Site-wide confirm modal** below for what that
actually does now (it no longer calls `window.confirm()`).

### Site-wide confirm modal: replaces `window.confirm()` for any `[data-confirm]` element

Every destructive action gated by `data-confirm` (News delete via `_card_menu.html`, user deletion
on `/users/`, and the Upload page's delete icon above) pops one shared, centered modal
(`#confirm-modal`/`#confirm-modal-overlay`, declared once in `base.html` so it's present on every
page) instead of the browser's native `window.confirm()` — a plain OS dialog looked out of place
against the rest of the site's gold-on-ink design system. Its confirm button uses a new `.btn-danger`
(red, `var(--danger)`) alongside the existing `.btn`/`.btn-outline` pair. The interception logic
lives in `card-menu.js` (not a new file — it already owned the one delegated `[data-confirm]` click
listener) and was deliberately widened from `.card-menu [data-confirm]` to a bare `[data-confirm]`
selector, so it now catches *any* such element anywhere on the page, not just menu items inside a
`.card-menu` dropdown. Confirming re-submits the button's parent `<form>` via `form.submit()` (which
— unlike a synthetic click — skips the button's own click handler, so it can't re-trigger the
prompt); cancelling, clicking the overlay, or Escape all just close it with no side effect.
`static/js/users-list.js` used to run its own near-identical `window.confirm()` check on
`.delete-user-form`'s `submit` event — that's now dead code eliminated outright, since the global
click listener's `preventDefault()` fires first and stops the native submit before that listener
would ever see it.

### Reusable "New" badge: `templates/_new_badge.html`

A small pill (`.news-new-badge` — red dot + "New") originally inline in `news.html` to flag the
single latest dispatch, pulled into its own partial so the same visual marker could be reused
anywhere a list has an obvious "newest" item. Usage is always the same shape: `{% if
<condition marking the newest item> %}{% include '_new_badge.html' %}{% endif %}` placed as the
first child inside the card. It is currently wired into four lists, each gating on both
"is this the newest-ordered item in the loop" and "am I on page 1 of the pagination" (so page 2+
never re-badges its own first row):
- `news.html` — `forloop.first` (News is always ordered `-created_at`, unpaginated).
- `writings_list.html` — `forloop.first and entries.number == 1`, generic across all three Writings
  categories (Fiction/Philosophy/Mythology), since each category's list is independently ordered
  `-created_at`.
- `godvalley_chapters.html` — `forloop.first and chapters.number == 1`, matching the list's
  `-chapter_number` ordering described above.
- `_archive_card.html` (used by `favourites.html`) — takes an optional `show_new_badge` include
  param rather than baking the condition into the partial itself, since `_archive_card.html` is
  reused by several pages (home, search, writings hub) that should never show the badge; only the
  caller that wants it passes `show_new_badge=True` for its first-page/first-item card. `Favourite`
  rows are ordered `-created_at`, so this marks the most recently favourited item, not the most
  recently published one.

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
  Ordered `-chapter_number` (newest chapter first, Chapter 1 sinks to the bottom) — a deliberate
  choice so readers land on the latest release first, matching how `writings_category_list` already
  sorts by `-created_at`. This is independent of `godvalley_detail`'s prev/next nav, which still
  queries by `chapter_number__lt`/`__gt` and is unaffected by list ordering.
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
`StyledPasswordChangeForm` subclasses Django's stock `PasswordChangeForm` (not `SetPasswordForm`),
so `/account/password/` requires the current password before accepting a new one. This used to be
the other way around — `SetPasswordForm`, deliberately with no current-password check, "removed at
explicit request; revisit once real account security is in scope" — until **agent-security**'s
audit (see **Custom Claude Code agents** below) flagged exactly that gap (a hijacked session cookie
alone was enough to permanently lock the real owner out) and this was confirmed as that revisit.

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
links to `/profile/`; Favourite, Reading List, Downloads, and News are real, account-backed drawer
items (see **Favourites and Reading List**, **Downloads: on-demand PDF export**, and **News**
above/below) — Bookmarks is deliberately gated `{% if user.is_staff %}` (visible to Mr. Dex only)
rather than shown to every visitor, since building it as a 4th near-identical "save this content"
toggle alongside Favourite/Reading List/Downloads would be redundant for regular visitors right now.
Candidate directions were analyzed but deferred pending a concrete decision: an in-chapter
reading-position bookmark (jump back to your exact scroll position — the one genuinely novel option,
since none of the other three track position within content, only whole-item state), custom
collections/folders (organize saved content beyond one flat Favourites list), or passage/quote
highlighting (Kindle-style). Once one of these (or something else) is greenlit and built, drop the
`is_staff` gate so it's visible to all visitors like the other drawer items.

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

### Favourites and Reading List: user-curated save actions, not auto-tracking

Both live in `upload/models.py` as near-identical models — `Favourite` and `ReadingListItem` —
each one row per `(user, content)` with a real `UniqueConstraint`, deliberately distinct from
`ReadingHistory` above: `ReadingHistory` is an automatic view log (recorded on every detail-page
visit), while these two are explicit visitor actions (a click), so neither shares a table or a
dedupe helper with it. Both follow the exact same shape end to end:

- **Icon buttons** — `_favourite_button.html` (heart) and `_reading_list_button.html` (open-book,
  the same SVG path as the drawer's Reading List icon) are both included from `writings_detail.html`
  and `godvalley_detail.html`, wrapped together in one `.hero-actions` flex container (`position:
  absolute; top/right: var(--gutter)`) at the top-right of the `.hero` section — `.hero` needed
  `position:relative` added for this to anchor against. Each button is a real `<form method="post">`
  (works with JS disabled) posting to a `toggle_*` view (`core.views.toggle_favourite` /
  `toggle_reading_list_item`), both `login_required`, both `get_or_create`-then-delete-if-not-created
  to toggle in one round trip, both gated to `is_published=True` content via `get_object_or_404`.
- **No full-page reload on click** — `static/js/favourite.js` and `static/js/reading-list.js` are
  near-duplicate site-wide delegated listeners (registered once in `base.html`, same pattern as
  `card-menu.js`) that intercept the form's `submit`, `fetch()` it with an
  `X-Requested-With: XMLHttpRequest` header, and toggle the button's `is-active` class/`aria-*`/SVG
  fill from the JSON response instead of letting the browser navigate. The views detect that header
  and branch: with it present, they return `JsonResponse({'is_favourited': ...})` /
  `JsonResponse({'is_in_reading_list': ...})`; without it (JS disabled), they fall back to a normal
  redirect using the form's hidden `next` field (`request.get_full_path` at render time) via the
  existing `_safe_next` helper — so the feature degrades to plain-form-and-reload rather than
  breaking outright.
- **List pages** — `/favourites/` and `/reading-list/` (`core.views.favourites` /
  `core.views.reading_list`, both `login_required`) render the user's saved items as
  `_archive_card.html` grids via `_paginate`, ordered `-created_at` (most recently
  favourited/saved first). Both are wired into the side drawer (`base.html`) — replacing what were
  previously dead `<button>` placeholders with real `<a href="{% url ... %}">` links — which is why
  the **What this is** intro above now calls out Favourite/Reading List as real rather than
  placeholder drawer items.

### Downloads: on-demand PDF export

A third `.hero-actions` icon (download-arrow, same SVG path as the drawer's Downloads icon)
sits alongside Favourite and Reading List on `writings_detail.html`/`godvalley_detail.html`, but
it isn't a toggle like the other two — it always performs the same action, so its button has no
`is-active` state and its own `<form>` (`_download_button.html`) is plain, un-JS'd `POST` to
`core.views.download_content`. That view does two things: builds a PDF on the fly via
`core.pdf.build_content_pdf` (see below) and returns it as
`HttpResponse(pdf_bytes, content_type='application/pdf')` with `Content-Disposition:
attachment; filename="<slug>.pdf"`. No JS interception was needed the way `favourite.js`/
`reading-list.js` prevent a full-page reload — a browser's response to a `Content-Disposition:
attachment` response is to pop the native download prompt/toolbar *without* navigating away from
the current page, so the plain form submit already behaves correctly with zero script.

`core/pdf.py` (a new small single-purpose module, alongside `feeds.py`/`sitemaps.py`/
`google_oauth.py` in the same "core owns one file per cross-cutting concern" pattern) uses
`reportlab` — added to `requirements.txt` — chosen specifically because it's a pure-Python wheel
with no system dependencies (unlike WeasyPrint, which needs GTK/Cairo/Pango installed separately
and is painful on Windows, the dev platform this project targets). It builds the PDF with
`reportlab.platypus.SimpleDocTemplate` + `Paragraph` flowables rather than manual `Canvas`
coordinate placement, so long chapter bodies get automatic word-wrap and page-breaks for free.
Body text is split into paragraphs the same way Django's `|linebreaks` filter would (blank-line-
separated blocks, with single `\n`s inside a block becoming `<br/>`), and every paragraph is run
through `xml.sax.saxutils.escape` before being handed to reportlab's `Paragraph` (which parses a
small HTML-like subset of its own), since raw chapter text could otherwise contain `<`/`&`/etc.
that would break reportlab's mini-parser. Dates are formatted via `django.utils.dateformat.format`
(`'F j, Y'`), not `datetime.strftime('%-d')` — `%-d` is a glibc/macOS-only strftime extension and
crashes on Windows (`%#d` is the Windows equivalent), so Django's own portable dateformat is used
instead of picking one platform-specific strftime flag over the other.

`upload.models.DownloadHistory` records what's been downloaded — one row per `(user, content)`,
`downloaded_at` as `auto_now` (not `auto_now_add`) so re-downloading bumps a row back to the top
instead of creating a duplicate, the exact same dedupe convention as `ReadingHistory` (chosen
because the user's own wording for this feature was "download **history**", unlike
Favourite/ReadingListItem's "saved item" framing above). The PDF itself is never written to disk
or `MEDIA_ROOT` — there is no `MEDIA_ROOT` configured in this project at all — it's regenerated
fresh from the `Content` row on every download, so `DownloadHistory` is purely a log, not a file
store; a "download again" button on `/downloads/` (`core.views.downloads`, `login_required`)
re-triggers `download_content` rather than serving a cached file. `/downloads/` deliberately
doesn't reuse the `_archive_card.html` grid the way `/favourites/` and `/reading-list/` do —
each row needs an independently-clickable re-download button next to the title link, which would
mean nesting a `<form>`/`<button>` inside `_archive_card.html`'s wrapping `<a>` (illegal, the same
problem `.stretched-link` solves for News) — so it instead reuses the `.reading-history-item` list-
row component from `/profile/`, wrapped in a new `.download-row` flex container that places the
re-download `<form>` as a sibling of the row's `<a>` rather than nested inside it.

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

A single global background image sits behind every page — `static/images/bg-cosmos.jpg` (a
black-hole/accretion-disk photo, converted from a much larger source PNG to a ~180KB JPEG via
Pillow, already available transitively through `reportlab` per **Downloads** above), wired into the
`body` rule in `static/css/style.css` rather than a template/DOM element, since a CSS
`background-image` always paints behind an element's children automatically — no extra wrapper
`<div>` or `z-index` bookkeeping needed against the navbar/drawer/modal layers already in
`base.html`. It's layered under a heavy `rgba(5,5,5,0.87)` gradient so it reads as ambience, not
decoration competing with body text — chapter/essay reading pages have no card behind their prose,
so the darken pass had to be tuned against actual long-form content, not just the hero.
`background-attachment:fixed` keeps it a single static backdrop instead of repeating per page; a
`max-width:900px` media query swaps it to `scroll` on touch viewports, since fixed backgrounds are a
known iOS Safari repaint quirk. Chosen deliberately over 3 other candidate space photos (a galaxy
field and two colorful nebulae) specifically because it's chromatically already on-brand — almost
entirely black with one gold/white focal ring — rather than introducing hues that would compete with
the site's strict two-color `--gold`/`--bg-primary` palette.

`.archive-grid`/`.archive-card` (used by home, Writings, God Valley chapters, News, Favourites,
Reading List, Search, and the Upload hub) renders fixed-size square cards, not the flexible
`minmax(320px, 1fr)` grid it started as — that `1fr` max let a lone card in a sparse category (e.g.
an empty Fiction list with one new entry) stretch to fill the entire row into a wide rectangle.
`grid-template-columns: repeat(auto-fit, minmax(min(380px, 100%), 380px))` fixes the max at 380px so
cards never grow past it, while the `min(380px, 100%)` half of the `minmax()` keeps the same rule
from overflowing on phones narrower than 380px; `justify-content:center` centers whatever cards
exist within a row — this specifically requires `auto-fit`, not `auto-fill`, since `auto-fill` keeps
phantom empty tracks that silently defeat centering (a sparse row still measures as "full" for
alignment purposes even though nothing renders in the empty tracks). Cards are `aspect-ratio:1/0.9`
(a fixed square would be `1/1`; this is intentionally a little shorter) with title/excerpt text
`-webkit-line-clamp`'d to 2/3 lines so overflowing text never breaks the fixed box — note
`-webkit-line-clamp` silently stops working if the clamped element is a direct flex item, which is
why `.archive-card` itself stays `display:block`, not `flex`, despite centering several children.
The Upload hub cards (`.upload-hub-card`) override back to `aspect-ratio:1/1` since their icon +
eyebrow + description + stat line need more vertical room than the plain list-style cards elsewhere.

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

## Custom Claude Code agents: agent-refactor, agent-cleancode, agent-security

Three project-scoped subagents live under `.claude/agents/` (`agent-refactor.md`,
`agent-cleancode.md`, `agent-security.md`) — Claude Code tooling checked into the repo, not
application code, so any future session can invoke them the same way rather than re-deriving an
audit approach from scratch each time.

All three share one deliberate design: exactly two explicit, user-triggered modes, never blended.
**FIND** (read-only, safe, the default) scans and reports — it must never write, edit, or delete a
file. **FIX** (write access) only runs on its own separate, explicit follow-up command (e.g. "fix
it", "clean these up") — a FIND report is never allowed to auto-escalate into edits on the same
turn. This mirrors the project's general "confirm before hard-to-reverse actions" norm, deliberately
applied to whole-codebase audits specifically so "audit this" and "now fix what you found" are
always two separately-authorized steps. Each agent's frontmatter also had to route around a real
YAML gotcha discovered while building the first one: a `description:` field written as a long
unquoted plain scalar breaks silently (and the agent fails to register at all) if it contains an
unescaped `": "` sequence anywhere, since YAML reads that as a new mapping key — the fix was to
keep the frontmatter `description` short and colon-safe and move the detailed mode explanation/
examples into the markdown body instead, which became the template all three agents followed.
Also worth knowing: a newly created or edited agent definition doesn't take effect in an
already-running session — the available-agent list loads once at session start, so a fresh session
(or IDE reconnect) is needed before a brand-new or just-edited agent can actually be invoked.

**`agent-refactor`** — finds, and on command fixes, cross-file code duplication and repo-wide
unused/dead code. Its brief explicitly excludes flagging this codebase's own deliberate shared
components (`_card_menu.html`/`card-menu.js`, `_archive_card.html`, the site-wide confirm modal,
etc.) as "duplication," since those exist specifically to be reused from one place. Its first
whole-repo FIND pass found 6 duplication clusters and 0 dead code; on command it fixed the 5
actionable ones (two were deliberately left alone as already-documented intentional parallel
structure, not oversights): (1) the God Valley vs. Writings public-URL branch was reimplemented 11
times across `core/views.py`, `core/feeds.py`, `core/sitemaps.py`, and 7 templates instead of using
`Content.get_absolute_url()`, which already existed — all 11 sites now call it; (2) `profile.js`,
`users-list.js`, and `news.js` each hand-rolled their own modal open/close logic that duplicated
what `card-menu.js`'s confirm-modal already generalized — `card-menu.js` gained shared
`openModal()`/`closeModal()` globals and the three page scripts were rewired onto them, keeping
only their own field-population logic local; (3) `godvalley_chapters.html` hand-inlined
`_archive_card.html`'s markup instead of including it — now does; (4) a new
`templates/_reading_history_row.html` partial replaced duplicated `.reading-history-item` markup
shared by `profile.html`/`downloads.html`; (5) a new `templates/_google_signin_button.html` partial
replaced the "Continue with Google" block duplicated verbatim between `login.html`/`signup.html`.

**`agent-cleancode`** — finds, and on command fixes, "ugly, irrelevant, and unreliable" code:
misleading naming/structure, dead comments/debug leftovers/stale TODOs, and concrete reliability
bugs — explicitly scoped away from `agent-refactor`'s duplication/dead-code territory, and
explicitly instructed not to fight this file's own stated philosophy (default to no comments unless
the WHY is genuinely non-obvious, no speculative validation/error-handling, no premature
abstraction — see **Doing tasks** norms this project inherits from the top-level Claude Code system
prompt). Its FIND pass found 4 issues and 0 "irrelevant" findings (no dead comments, debug
leftovers, or stale TODOs turned up anywhere in the codebase). Fixed on command: (1)
`godvalley_detail` could 500 if a God Valley chapter's `chapter_number` was left blank (the model
field is nullable, shared with Fiction, but the view's prev/next lookup unconditionally compares
against it) — `GodValleyUploadForm` now makes `chapter_number` required, an intentional behavior
change closing off the invalid state entirely; (2) `SECRET_KEY` was a hardcoded
`startproject`-default literal committed to git, in a repo where every other secret already flows
through `.env` — rotated to a freshly generated value, moved into `.env`, and read via
`os.environ['SECRET_KEY']` (mandatory, matching the `DB_*` convention); the old committed key is
permanently burned and never reused. (3) `main.js`'s link fade-transition effect wasn't
re-registered inside `initPageEffects()`, so it silently broke on any link rendered via
`list-filters.js`'s AJAX soft-navigation — moved inside, matching the file's own documented
re-registration convention. (4) `main.js`/`list-filters.js` used a two-statement-per-line
formatting style found nowhere else in the JS codebase — reflowed to match.

**`agent-security`** — a full security audit specialist: injection, auth/access-control gaps,
exposed secrets (working tree *and* git history, not just HEAD), OWASP-class web vulnerabilities,
crypto/data-protection issues, config/deployment hardening, dependency CVEs, and malicious/
backdoor-shaped code. Positioned as this repo's authoritative source for anything
security-classified, deferring pure quality/duplication concerns to the other two agents. Every
finding has to trace to a concrete, real exploit scenario in this codebase's actual configuration,
not a generic checklist hit — and the report has to explicitly list what was checked and ruled safe,
not just what's wrong, so a clean result reads as verified rather than skipped. Its first whole-repo
FIND pass came back 0 Critical/High, 5 Medium, 2 Low, with SQL/command injection, XSS, CSRF, open
redirects, SSRF, clickjacking, IDOR, privilege escalation via forms, and all `requirements.txt` pins
verified clean — and it independently re-confirmed the `SECRET_KEY` rotation above was actually
closed (old key dead, `.env` untracked, never reused). Findings, fixed on command across two rounds
(6 of 7 — email verification was deliberately deferred, see below): **DEBUG** now defaults to
`'False'` when unset (fails closed on a forgotten `.env`, instead of the previous fail-open
default), with an explicit `DEBUG=True` line added to the actual `.env` so local dev behavior
didn't change. **Password change** now requires the current password — see the **Visitor auth**
section above; this is exactly the "revisit once real account security is in scope" this file
already called for. **Production cookie/HSTS hardening** (`SESSION_COOKIE_SECURE`,
`CSRF_COOKIE_SECURE`, `SECURE_SSL_REDIRECT`, `SECURE_HSTS_SECONDS`,
`SECURE_HSTS_INCLUDE_SUBDOMAINS`) was added, gated on `not DEBUG` so it's dormant on today's local
dev and activates automatically the moment a real deployment runs with `DEBUG=False`. **Login
throttling** was added to `login_view` (`core/views.py`) — 5 failed attempts locks out for 15
minutes, keyed by both IP and attempted email independently, built entirely on Django's cache
framework rather than a new dependency like `django-axes`. **`edit_user`** now refuses to
deactivate a staff/superuser target, mirroring the guard `delete_user` already had. **Unpublished
content's cover images staying reachable via a guessed direct `/media/` URL** was investigated and
deliberately left unfixed — properly closing it needs a new authenticated media-serving view
rewired across roughly a dozen templates, which the agent's own FIX-mode rules correctly treat as
too large a change to force through a contained fix rather than as something to paper over.

**No email verification at signup** (the 7th finding) was deferred rather than fixed inline, since
closing it required a real infrastructure decision (an email backend) the codebase didn't have yet.
That decision was made in the same session, just not through the agent: **Gmail SMTP OTP
verification at signup** — `core/otp.py` (a new small single-purpose module, same "core owns one
file per cross-cutting concern" pattern as `google_oauth.py`/`feeds.py`/`sitemaps.py`/`pdf.py`),
optional and self-hiding exactly like `google_oauth.is_configured()` (unset `EMAIL_HOST_USER`/
`EMAIL_HOST_PASSWORD` in `.env` and signup activates accounts immediately, unchanged from before
this feature existed). When configured, `signup` creates the account with `is_active=False`,
emails a 6-digit code (`secrets`-grade random, cache-backed with a 10-minute TTL, attempt-limited
to 5 tries, resend-cooldown 60s — no new model/migration needed), and a new `/signup/verify/`
page (`core.views.verify_email`/`resend_otp`, `templates/verify_email.html`) activates the account
and logs the visitor in once the code matches. Deliberately reuses the existing `is_active` field
rather than adding a new column — the same field an admin already uses to deactivate someone on
`/users/`, so an unverified signup and an admin-deactivated account currently look identical on the
Users list; acceptable for now given this is a personal single-author site, revisit with a distinct
status badge if that ambiguity ever actually matters. Chosen over a third-party transactional email
provider specifically because it needs no domain/DNS setup — just a Gmail account's app password
(`myaccount.google.com/apppasswords`) — matching this project's general preference for
zero-infrastructure options (e.g. `reportlab` over WeasyPrint for the same reason, see **Downloads**
above).

## Planned next: SEO for the site's mechanics, not its content

The next round of work planned is SEO — but scoped deliberately to the *website*, not the
*content*. Fiction/Philosophy/Mythology/God Valley chapters and News dispatches are fictional and
personal creative writing, not informational articles written to satisfy search intent — so
content-level SEO tactics (keyword targeting, rewriting prose for search engines, per-chapter meta
descriptions optimized for click-through rather than for a reader) don't apply here and shouldn't
be done. The actual SEO work belongs at the site's technical/structural layer instead: things like
`core/sitemaps.py`'s `ContentSitemap`/`StaticViewSitemap` and `core/feeds.py`'s `LatestContentFeed`
(see **Syndication / SEO** above) are the right kind of surface to extend — page titles/meta
descriptions, structured data, crawlability, canonical URLs, performance — not the prose itself.
