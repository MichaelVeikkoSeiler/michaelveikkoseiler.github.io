#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Entfernt aus der gespiegelten Site die WordPress-Reste, die statisch tot sind.
Das Design bleibt unangetastet - entfernt wird nur, was ohne PHP ohnehin
nichts mehr tut (REST-API-Verweise, Feeds, oEmbed, Contact Form 7, Suche).
"""

import os
import re
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "site"))

# Head-Elemente, die auf PHP-Endpunkte zeigen und statisch ins Leere laufen
DEAD_TAGS = [
    (r"""<link[^>]*\brel=["']shortlink["'][^>]*>\s*""", "shortlink"),
    (r"""<link[^>]*\brel=["']EditURI["'][^>]*>\s*""", "RSD/EditURI"),
    (r"""<link[^>]*\bwlwmanifest[^>]*>\s*""", "wlwmanifest"),
    (r"""<link[^>]*\brel=["']https://api\.w\.org/["'][^>]*>\s*""", "REST-API-Link"),
    (r"""<link[^>]*\btype=["']application/(?:json|xml)\+oembed["'][^>]*>\s*""", "oEmbed"),
    (r"""<link[^>]*\btype=["']application/rss\+xml["'][^>]*>\s*""", "RSS-Feeds"),
    (r"""<meta[^>]*\bname=["']generator["'][^>]*>\s*""", "generator-Meta"),
    # WordPress-Emoji-Loader (inline Script + zugehoeriges CSS)
    (r"""<script[^>]*>\s*window\._wpemojiSettings.*?</script>\s*""", "Emoji-Loader"),
    (r"""<style[^>]*>\s*img\.wp-smiley.*?</style>\s*""", "Emoji-CSS"),
    # Contact Form 7 - auf der Seite existiert kein einziges Formular
    (r"""<link[^>]*contact-form-7[^>]*>\s*""", "CF7-CSS"),
    (r"""<script[^>]*contact-form-7[^>]*></script>\s*""", "CF7-JS"),
    (r"""<script[^>]*id=["']contact-form-7-js-extra["'][^>]*>.*?</script>\s*""", "CF7-Config"),
    # WordPress-Suchformular - ohne PHP nicht funktionsfaehig
    (r"""<form[^>]*class=["']search["'][^>]*>.*?</form>\s*""", "Suchformular"),
]

# Verzeichnisse, die nur PHP-Endpunkte gespiegelt haben
DEAD_DIRS = ["wp-json", "feed", "comments"]

counts = {}


def clean_html():
    files = 0
    for root, _dirs, names in os.walk(SITE):
        for fn in names:
            if not fn.endswith(".html"):
                continue
            p = os.path.join(root, fn)
            text = open(p, encoding="utf-8").read()
            orig = text
            for pat, label in DEAD_TAGS:
                text, n = re.subn(pat, "", text, flags=re.S | re.I)
                if n:
                    counts[label] = counts.get(label, 0) + n
            # /index.html -> / (kosmetisch, Wurzel-Links)
            text, n = re.subn(r"""(\b(?:href|action|content)=["'])/index\.html(["'])""",
                              r"\1/\2", text)
            if n:
                counts["/index.html -> /"] = counts.get("/index.html -> /", 0) + n
            if text != orig:
                open(p, "w", encoding="utf-8").write(text)
                files += 1
    return files


def drop_dirs():
    for d in DEAD_DIRS:
        p = os.path.join(SITE, d)
        if os.path.isdir(p):
            n = sum(len(f) for _r, _d, f in os.walk(p))
            shutil.rmtree(p)
            counts["Verzeichnis /%s/ (%d Dateien)" % (d, n)] = 1
    # verwaiste feed/-Unterordner (z.B. portfolio_category/*/feed/)
    for root, dirs, _f in os.walk(SITE, topdown=False):
        if os.path.basename(root) == "feed":
            shutil.rmtree(root, ignore_errors=True)
            counts["feed-Unterordner"] = counts.get("feed-Unterordner", 0) + 1


def main():
    files = clean_html()
    drop_dirs()
    print("Bereinigt: %d HTML-Dateien angepasst.\n" % files)
    for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
        print("  %-34s %s" % (k, v))


if __name__ == "__main__":
    main()
