#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Vergleicht den sichtbaren Text jeder Seite mit dem der noch laufenden
Original-Seite auf www.bildstudio.ch.

Hintergrund: rewrite.py schreibt absolute URLs auf relative Pfade um und trifft
dabei gelegentlich auch Text, der für Leser bestimmt ist - so wurde aus
"Webseite: https://www.bildstudio.ch/" im Impressum einmal "Webseite: /index.html".
Solche Treffer fallen sonst niemandem auf.

Absichtliche Abweichungen (Jahreszahl, Mailadresse) werden als solche gemeldet -
das Skript sagt, was sich unterscheidet, nicht ob es falsch ist.

    python3 tools/difftext.py

Funktioniert nur, solange die alte Seite online ist.
"""

import os
import re
import sys
import html
import difflib
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "docs"))
BASE = "https://www.bildstudio.ch"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")


def visible(markup):
    """Reduziert HTML auf den Text, den ein Besucher tatsächlich liest."""
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", markup, flags=re.S)
    t = re.sub(r"<[^>]+>", " ", t)
    t = html.unescape(t)
    return [ln.strip() for ln in re.sub(r"[ \t]+", " ", t).split("\n") if ln.strip()]


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=45) as r:
        return r.read().decode("utf-8", "ignore")


def main():
    pages = []
    for root, _d, files in os.walk(SITE):
        if "index.html" in files:
            rel = os.path.relpath(root, SITE).replace(os.sep, "/")
            pages.append("/" if rel == "." else "/" + rel + "/")
    pages.sort()

    changed = failed = 0
    for path in pages:
        local = os.path.join(SITE, path.strip("/"), "index.html")
        try:
            remote = fetch(BASE + path)
        except Exception as e:  # noqa: BLE001
            print("  ? %-42s nicht abrufbar (%s)" % (path, str(e)[:40]))
            failed += 1
            continue

        a, b = visible(remote), visible(open(local, encoding="utf-8").read())
        diff = [ln for ln in difflib.unified_diff(a, b, lineterm="", n=0)
                if ln[:1] in "+-" and ln[:3] not in ("---", "+++")]
        if diff:
            changed += 1
            print("\n--- %s" % path)
            for ln in diff[:8]:
                print("   %s %s" % (ln[0], ln[1:].strip()[:140]))

    print("\n%d von %d Seiten weichen im Text ab, %d nicht abrufbar."
          % (changed, len(pages), failed))
    return 0


if __name__ == "__main__":
    sys.exit(main())
