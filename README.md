# Rhema — Bible study app (web build)

The single-file Rhema Bible study app, published so it can be opened in any browser.

**Open it:** https://son-of-melchizedek.github.io/rhema-app/

## What this is

`index.html` is the entire app — markup, styles, logic and content in one
self-contained file. No build step, no dependencies, no server. Open it and it runs.

Shipped to Android as a WebView APK from the same file.

## Features

- Scripture reading with multiple translations
- Courses (sample courses work fully offline; custom courses generate via AI)
- Reading plans, devotionals, prayer journal, reading goals
- Bible character profiles and a topical index
- AI study companion — verse study modes, context, Hebrew/Greek, Ask Rhema
- Discover — curated teaching channels and playlists

## AI features

The build currently ships **with** the DeepSeek provider key baked in, so the AI study
features (Ask Rhema, verse study modes, custom plans/courses) work for anyone who opens
the link — no setup. The trade-off is deliberate: anything in a static page is
extractable, so treat that key as public and rotate it if it is abused. The OpenCode Go
preset also carries its key, but that host sends no CORS headers, so it cannot be used
from a web page (it works only inside the Android WebView build).

To publish a keyless build instead (visitors paste their own key in
**Settings → AI Provider Settings**), run `bash publish.sh --no-keys`.

## Visibility

GitHub Pages has no "unlisted" mode: the URL is open to anyone who has it, and a private
repository does not hide the site (and on GitHub Free it stops Pages serving entirely).
This repo therefore publishes a `robots.txt` disallow plus a `noindex` meta tag, which
keeps the site out of search engines. That is discoverability control, **not** access
control — for real gating, put the site behind Cloudflare Access or a password-protected
host.

## Secrets

The source-of-truth app file lives in a private repository (`Son-of-Melchizedek/rhema`),
which is where it is edited and packaged. Publishing is done with `publish.sh`; the
`--no-keys` mode scrubs provider keys and fails closed if any key-shaped token survives.

## Provenance

Built from the private `rhema` repo's app file, post-Lionheart-removal build.
