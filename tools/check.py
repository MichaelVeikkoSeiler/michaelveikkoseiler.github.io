#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft die statische Site: existiert jede referenzierte Datei wirklich?
Meldet tote interne Links und listet verbleibende externe Abhängigkeiten.
"""

import os
import re
import sys
import urllib.parse
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "docs"))

ATTR_RE = re.compile(
    r"""(?:href|src|data-src|data-original|data-bg|poster|data-thumb)\s*=\s*["']([^"']+)["']""", re.I)
SRCSET_RE = re.compile(r"""(?:srcset|data-srcset)\s*=\s*["']([^"']+)["']""", re.I)
CSSURL_RE = re.compile(r"""url\(\s*['"]?([^'")]+?)['"]?\s*\)""", re.I)

broken = defaultdict(list)   # ziel -> [quellen]
external = defaultdict(int)
ok = 0


def exists(rel):
    """rel ist ein wurzel-relativer Pfad wie /kontakt/ oder /wp-content/x.jpg"""
    p = os.path.join(SITE, urllib.parse.unquote(rel).lstrip("/"))
    if os.path.isfile(p):
        return True
    if os.path.isdir(p) and os.path.isfile(os.path.join(p, "index.html")):
        return True
    if os.path.isfile(p.rstrip("/") + "/index.html"):
        return True
    return False


def check_file(path):
    global ok
    rel_src = "/" + os.path.relpath(path, SITE).replace(os.sep, "/")
    try:
        text = open(path, encoding="utf-8").read()
    except (UnicodeDecodeError, OSError):
        return

    refs = set()
    for m in ATTR_RE.finditer(text):
        refs.add(m.group(1))
    for m in SRCSET_RE.finditer(text):
        for part in m.group(1).split(","):
            c = part.strip().split()
            if c:
                refs.add(c[0])
    for m in CSSURL_RE.finditer(text):
        refs.add(m.group(1))

    base_dir = os.path.dirname(rel_src)
    for r in refs:
        r = r.strip()
        if not r or r.startswith(("data:", "mailto:", "tel:", "#", "javascript:")):
            continue
        if re.match(r"^(https?:)?//", r):
            host = urllib.parse.urlsplit(
                r if r.startswith("http") else "https:" + r).netloc.lower()
            external[host] += 1
            continue
        target = r.split("#")[0].split("?")[0]
        if not target:
            continue
        if not target.startswith("/"):
            target = os.path.normpath(os.path.join(base_dir, target)).replace(os.sep, "/")
            if not target.startswith("/"):
                target = "/" + target
        if exists(target):
            ok += 1
        else:
            broken[target].append(rel_src)


def main():
    for root, _d, files in os.walk(SITE):
        for fn in files:
            if os.path.splitext(fn)[1].lower() in (".html", ".css", ".js", ".svg"):
                check_file(os.path.join(root, fn))

    print("Geprüfte interne Referenzen: %d in Ordnung, %d tot.\n" % (ok, len(broken)))
    if broken:
        print("TOTE LINKS:")
        for t, srcs in sorted(broken.items()):
            print("  %-60s  <- %s%s" % (
                t[:60], srcs[0], (" +%d weitere" % (len(srcs) - 1)) if len(srcs) > 1 else ""))
    print("\nVerbleibende externe Hosts (Requests beim Laden):")
    for h, n in sorted(external.items(), key=lambda kv: -kv[1]):
        print("  %-32s %d" % (h, n))
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main())
