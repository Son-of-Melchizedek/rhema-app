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

## AI features need a key

This published build ships with **no API key** (`DEFAULT_AI.key` is empty). Everything
offline works out of the box. To use the AI study features, open **Settings → AI Provider
Settings** and paste your own OpenAI-compatible API key. It is stored locally in your
browser and never sent anywhere except your chosen provider.

## Secrets

The source-of-truth app file lives in a private repository, which is where it is edited and
packaged. This repo is generated from it and is scrubbed on every sync — provider keys are
removed before publication and the scrub fails closed.

## Provenance

Built from the private `rhema` repo's app file, post-Lionheart-removal build.
