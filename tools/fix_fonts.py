#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repariert die Google-Fonts-Einbindung.

Beim Spiegeln landeten beide Font-Stylesheets (Poppins und Oswald) unter
demselben Dateinamen - Oswald hat Poppins überschrieben. Hier werden beide
sauber getrennt geladen, die Schriftdateien lokalisiert und die <link>-Tags
in allen HTML-Seiten korrigiert.

Ausserdem: tote dns-prefetch- und wp-json-Verweise entfernen.
"""

import os
import re
import glob
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
SITE = os.path.abspath(os.path.join(HERE, "..", "docs"))
EXT = os.path.join(SITE, "_ext")

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/122.0 Safari/537.36")

FONTS = [
    ("bauman-main-font-css", "https://fonts.googleapis.com/css?family=Poppins:300,400,600,700",
     "_ext/fonts.googleapis.com/poppins.css"),
    ("bauman-secondary-font-css", "https://fonts.googleapis.com/css?family=Oswald:400,700",
     "_ext/fonts.googleapis.com/oswald.css"),
]


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def main():
    # 1) Beide Stylesheets getrennt holen, Schriftdateien lokalisieren
    for _id, url, rel in FONTS:
        css = get(url).decode("utf-8")
        fams = sorted(set(re.findall(r"font-family: '([^']+)'", css)))
        for m in sorted(set(re.findall(r"url\((https://fonts\.gstatic\.com/[^)]+)\)", css))):
            p = urllib.parse.urlsplit(m).path.lstrip("/")
            dest = os.path.join(EXT, "fonts.gstatic.com", p)
            if not os.path.isfile(dest):
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                open(dest, "wb").write(get(m))
            css = css.replace(m, "/_ext/fonts.gstatic.com/" + p)
        out = os.path.join(SITE, rel)
        os.makedirs(os.path.dirname(out), exist_ok=True)
        open(out, "w", encoding="utf-8").write(css)
        n = len(re.findall(r"@font-face", css))
        print("%-28s -> %s  (%s, %d Schnitte)" % (_id, rel, ", ".join(fams), n))

    # 2) <link>-Tags in allen HTML-Seiten auf die neuen Dateien zeigen lassen
    changed = 0
    for p in glob.glob(os.path.join(SITE, "**", "*.html"), recursive=True):
        t = open(p, encoding="utf-8").read()
        o = t
        for _id, _url, rel in FONTS:
            t = re.sub(
                r"""(<link[^>]*\bid=['"]%s['"][^>]*\bhref=['"])[^'"]*(['"])""" % re.escape(_id),
                r"\g<1>/%s\g<2>" % rel, t)
        # tote Verweise raus
        t = re.sub(r"""<link[^>]*\brel=['"]dns-prefetch['"][^>]*>\s*""", "", t)
        t = re.sub(
            r"""<link[^>]*\brel=['"]alternate['"][^>]*\bhref=['"]/wp-json/[^'"]*['"][^>]*>\s*""",
            "", t)
        t = re.sub(
            r"""<link[^>]*\bhref=['"]/wp-json/[^'"]*['"][^>]*\brel=['"]alternate['"][^>]*>\s*""",
            "", t)
        if t != o:
            open(p, "w", encoding="utf-8").write(t)
            changed += 1

    # 3) alte Sammeldatei entfernen
    old = os.path.join(EXT, "fonts.googleapis.com", "css")
    if os.path.isdir(old):
        for r, _d, fs in os.walk(old, topdown=False):
            for f in fs:
                os.remove(os.path.join(r, f))
            os.rmdir(r)
        print("alte Sammeldatei _ext/fonts.googleapis.com/css/ entfernt")

    print("\n%d HTML-Dateien angepasst." % changed)


if __name__ == "__main__":
    main()
