# Rhema — Bible study app (web build)

The single-file Rhema Bible study app, published so it can be opened in any browser.

**Open it:** https://son-of-melchizedek.github.io/rhema-app/

## What this is

`index.html` is the entire app — markup, styles, logic and content in one
self-contained file. No build step, no dependencies, no server. Open it and it runs.

This build is the **Android APK's asset file, published as-is**: `index.html` was extracted
from `Rhema.apk` (`assets/rhema.html`), and the pinned-chrome tour fix from the Oct 19 web
build was ported back in — the APK predates it, and without it the Library steps and the
final tour step dead-end with no way forward.

Shipped to Android as a WebView APK from the same file.

## Features

- Scripture reading with multiple translations
- Courses (sample courses work fully offline; custom courses generate via AI)
- Reading plans, devotionals, prayer journal, reading goals
- Bible character profiles and a topical index
- AI study companion — verse study modes, context, Hebrew/Greek, Ask Rhema
- Discover — curated teaching channels and playlists

## AI features — read this before reporting "AI is broken"

The app calls the provider **from the browser**, and `opencode.ai` (the fast default)
answers a CORS preflight with 404. A browser on a static host therefore cannot reach it,
and no amount of key pasting fixes that. The app knows: on launch it probes a same-origin
`/proxy/ai/` hop, and only when that hop exists does it keep the OpenCode provider.

- **On this GitHub Pages link** there is no hop, so the app falls back to the OpenRouter
  preset with an empty key. Paste your own key in **Settings → AI Provider Settings** and
  every AI feature works. That is by design, not a fault.
- **Running it locally gives zero-setup AI.** `rhema-server.py` in this repo serves the
  app *and* the `/proxy/ai/` hop, so the shipped OpenCode key is used server-side, where
  CORS does not apply:

  ```bash
  python rhema-server.py          # http://127.0.0.1:8092/
  bash start.sh                   # same, plus opens the browser
  ```

  Upstreams are allowlisted (https + host list) so the hop cannot be used as an SSRF
  relay, and it holds no key of its own — it forwards the browser's headers untouched.

Do not re-scrub the keys on a normal publish: the shipped OpenCode key measures **200**
upstream, while the shipped DeepSeek direct key answers **402 Insufficient Balance**.

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

Built from the APK asset file of the Oct 2026 build, with the Oct 19 tour fix re-applied.
`rhema-intro.mp4` and `rhema-intro-poster.jpg` are siblings of `index.html` on purpose —
the app references them relatively and silently falls back to its canvas intro if they 404.
