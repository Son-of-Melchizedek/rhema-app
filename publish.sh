#!/usr/bin/env bash
# Publish the single-file Rhema app to the public Pages site.
#
#   bash publish.sh            # ship WITH provider keys (AI works for link holders)
#   bash publish.sh --no-keys  # scrub provider keys (AI requires the visitor's own key)
#
# Two things differ from the private source file:
#   1. provider keys may be scrubbed (--no-keys) so a public page cannot be farmed
#      for the owner's API balance. WITH keys is the default because the shared
#      church build is expected to have AI working out of the box.
#   2. a noindex robots meta tag + robots.txt are injected: GitHub Pages cannot make
#      a site "unlisted", so this is the only lever that keeps it out of search
#      engines. It is NOT access control — anyone holding the URL can open it.
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIVE="${RHEMA_LIVE:-$HOME/content/rhema.html}"
MODE="${1:-}"

cp "$LIVE" "$REPO/index.html"

if [[ "$MODE" == "--no-keys" ]]; then
  python3 "$REPO/scrub_keys.py" "$REPO"
else
  echo "WARNING: publishing WITH provider keys — anyone who opens the URL can extract them."
  grep -c "key:'sk-" "$REPO/index.html" | sed 's/^/  key-shaped tokens present: /'
fi

python3 - "$REPO/index.html" <<'PY'
import re, sys
p = sys.argv[1]
s = open(p, encoding='utf-8').read()
tag = '<meta name="robots" content="noindex,nofollow,noarchive">'
if 'name="robots"' not in s:
    s = s.replace('<head>', '<head>\n' + tag, 1)
open(p, 'w', encoding='utf-8').write(s)
print('noindex meta:', 'present' if tag in open(p, encoding='utf-8').read() else 'MISSING')
PY

printf 'User-agent: *\nDisallow: /\n' > "$REPO/robots.txt"
echo "wrote robots.txt (Disallow: /)"
# Publish for real. Previously this script only staged the file and printed a
# "next:" hint, so a commit without a push looked like a successful deploy while
# the live site kept serving the previous build. That is how a fix sat verified
# locally and missing in production.
cd "$REPO"
if git diff --quiet --cached && git diff --quiet; then
  echo "no changes to publish"
else
  git add -A
  git commit -q -m "${RHEMA_MSG:-Rhema app update}" || echo "(nothing to commit)"
fi
git push -q origin HEAD && echo "pushed: $(git log --oneline -1)"

# Prove the deploy actually happened rather than trusting the push.
REMOTE_SHA=$(git rev-parse HEAD)
for i in 1 2 3 4 5 6 7 8 9 10; do
  sleep 6
  LIVE_SHA=$(curl -s "${RHEMA_URL:-https://son-of-melchizedek.github.io/rhema-app/}" | sha256sum | cut -d' ' -f1)
  SRC_SHA=$(sha256sum index.html | cut -d' ' -f1)
  if [[ "$LIVE_SHA" == "$SRC_SHA" ]]; then
    echo "verified live matches published build (${SRC_SHA:0:16})"
    exit 0
  fi
done
echo "WARNING: live site does not match the build yet (want ${SRC_SHA:0:16}, got ${LIVE_SHA:0:16})"
exit 1
