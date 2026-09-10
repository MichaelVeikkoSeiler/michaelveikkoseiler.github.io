#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Schreibt in der gespiegelten Site alle absoluten URLs auf wurzel-relative Pfade um,
damit die Seite ohne Verbindung zur alten WordPress-Installation läuft.

Behandelt:
  * https://www.bildstudio.ch/... und https://bildstudio.ch/...
  * protokoll-relative //www.bildstudio.ch/...
  * JSON-escapte Form https:\\/\\/www.bildstudio.ch\\/...
  * externe Hosts (FontAwesome, Google Fonts) -> /_ext/<host>/...
"""

import os
import re
import sys
import json
import urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from mirror import norm, local_path, web_path, BASE_HOST, EXT_HOSTS  # noqa: E402

SITE = os.path.abspath(os.path.join(HERE, "..", "docs"))

TEXT_EXT = {".html", ".htm", ".css", ".js", ".json", ".xml", ".svg", ".txt", ".webmanifest"}

# Nur Assets externer Hosts umschreiben, die wir wirklich haben
have = set()
for root, _dirs, files in os.walk(SITE):
    for fn in files:
        rel = os.path.relpath(os.path.join(root, fn), SITE).replace(os.sep, "/")
        have.add("/" + rel)
        if rel.endswith("/index.html"):
            have.add("/" + rel[: -len("index.html")])

PLAIN_RE = re.compile(
    r"""(?:https?:)?//(?:www\.)?bildstudio\.ch(/[^\s"'<>)\]\\]*)?""", re.I)
ESCAPED_RE = re.compile(
    r"""https?:\\/\\/(?:www\.)?bildstudio\.ch((?:\\/[^\s"'<>)\]\\]*)*)""", re.I)
EXT_RE = re.compile(
    r"""(?:https?:)?//(%s)(/[^\s"'<>)\]\\]*)?""" % "|".join(
        re.escape(h) for h in sorted(EXT_HOSTS)), re.I)

stats = {"plain": 0, "escaped": 0, "ext": 0, "files": 0}


def map_local(url):
    """URL -> wurzel-relativer lokaler Pfad, oder None wenn nicht abbildbar."""
    u = norm(url)
    if not u:
        return None
    return web_path(u)


def sub_plain(m):
    path = m.group(1) or "/"
    wp = map_local("https://%s%s" % (BASE_HOST, path))
    if not wp:
        return m.group(0)
    stats["plain"] += 1
    return wp


def sub_escaped(m):
    path = (m.group(1) or "").replace("\\/", "/") or "/"
    wp = map_local("https://%s%s" % (BASE_HOST, path))
    if not wp:
        return m.group(0)
    stats["escaped"] += 1
    return wp.replace("/", "\\/")


def sub_ext(m):
    host, path = m.group(1).lower(), m.group(2) or "/"
    u = norm("https://%s%s" % (host, path))
    if not u:
        return m.group(0)
    wp = web_path(u)
    if wp not in have:
        return m.group(0)          # nicht gespiegelt -> Original-CDN behalten
    stats["ext"] += 1
    return wp


def main():
    for root, _dirs, files in os.walk(SITE):
        for fn in files:
            if os.path.splitext(fn)[1].lower() not in TEXT_EXT:
                continue
            p = os.path.join(root, fn)
            try:
                raw = open(p, "rb").read()
                text = raw.decode("utf-8")
            except (UnicodeDecodeError, OSError):
                continue
            new = ESCAPED_RE.sub(sub_escaped, text)
            new = PLAIN_RE.sub(sub_plain, new)
            new = EXT_RE.sub(sub_ext, new)
            if new != text:
                open(p, "wb").write(new.encode("utf-8"))
                stats["files"] += 1

    print("Umgeschrieben in %d Dateien:" % stats["files"])
    print("  %d absolute URLs, %d escapte URLs, %d externe Assets"
          % (stats["plain"], stats["escaped"], stats["ext"]))


if __name__ == "__main__":
    main()
