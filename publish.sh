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
echo
echo "next:"
echo "  git -C \"$REPO\" add -A && git -C \"$REPO\" commit -m '...' && git -C \"$REPO\" push"
