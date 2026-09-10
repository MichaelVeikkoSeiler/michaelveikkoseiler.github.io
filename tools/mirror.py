#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Spiegelt www.bildstudio.ch als statische Website nach ../docs/.

Vorgehen:
  1. Seiten entdecken (Sitemaps + Links im HTML), BFS auf gleicher Domain.
  2. Alle referenzierten Assets sammeln (HTML-Attribute, CSS url(), inline styles).
  3. CSS rekursiv nach weiteren Assets/Fonts durchsuchen.
  4. Absolute URLs global auf wurzel-relative Pfade umschreiben.

Externe Hosts (FontAwesome, Google Fonts) werden nach /_ext/<host>/... lokalisiert,
damit die Seite ohne fremde CDNs auskommt.
"""

import os
import re
import sys
import json
import gzip
import time
import queue
import threading
import urllib.parse
import urllib.request
import urllib.error

BASE_HOST = "www.bildstudio.ch"
BASE = "https://" + BASE_HOST
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
OUT = os.path.abspath(OUT)

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
      "(KHTML, like Gecko) Version/17.0 Safari/605.1.15")

# Externe Hosts, die mitgespiegelt werden sollen
EXT_HOSTS = {
    "use.fontawesome.com",
    "fonts.googleapis.com",
    "fonts.gstatic.com",
    "kit.fontawesome.com",
    "ka-f.fontawesome.com",
}

lock = threading.Lock()
seen_urls = set()      # bereits eingeplante URLs
saved = {}             # url -> lokaler Pfad (relativ zu OUT, mit /)
failed = {}            # url -> Fehler
pages = set()          # URLs, die als HTML-Seite gespeichert wurden

# ---------------------------------------------------------------- Hilfsfunktionen

def norm(url, base=BASE):
    """Absolutiert und normalisiert eine URL. Gibt None bei uninteressanten URLs."""
    if not url:
        return None
    url = url.strip().replace("&amp;", "&")
    if url.startswith(("data:", "mailto:", "tel:", "javascript:", "#", "about:", "blob:")):
        return None
    url = urllib.parse.urljoin(base, url)
    p = urllib.parse.urlsplit(url)
    if p.scheme not in ("http", "https"):
        return None
    host = p.netloc.lower()
    if host == "bildstudio.ch":
        host = BASE_HOST
    if host != BASE_HOST and host not in EXT_HOSTS:
        return None
    path = p.path
    # Offensichtlicher Müll aus inline-JS / meta-Tags
    if re.search(r"[\s+]", path) or "%20" in path:
        return None
    # Fragment weg, ver-Query weg (WordPress Cache-Buster)
    q = p.query
    if q:
        keep = [kv for kv in q.split("&")
                if not kv.startswith(("ver=", "v=", "_=", "m="))]
        q = "&".join(keep)
    if host == BASE_HOST:
        # ?p=123 / ?page_id= sind Shortlinks auf bereits erfasste Seiten
        if re.match(r"^(p|page_id|cat|attachment_id)=", q or ""):
            return None
        # Doppelte Slashes und fehlender Trailing-Slash bei Seiten
        path = re.sub(r"/{2,}", "/", path) or "/"
        ext = os.path.splitext(os.path.basename(path))[1]
        if not ext and not path.endswith("/"):
            path += "/"
    return urllib.parse.urlunsplit(("https", host, path, q, ""))


def local_path(url):
    """Bildet eine URL auf einen lokalen Dateipfad (relativ, ohne führenden /) ab."""
    p = urllib.parse.urlsplit(url)
    host = p.netloc.lower()
    path = urllib.parse.unquote(p.path)
    prefix = "" if host == BASE_HOST else "_ext/" + host + "/"

    # Query in den Dateinamen kodieren (z.B. Google-Fonts CSS)
    suffix = ""
    if p.query:
        suffix = "_" + re.sub(r"[^A-Za-z0-9]+", "-", p.query)[:60]

    if path.endswith("/") or path == "":
        # Verzeichnis -> index.html
        return (prefix + path.lstrip("/") + "index.html").replace("//", "/")

    name = os.path.basename(path)
    if "." not in name:
        # extensionslose Seite -> hübsche URL als Verzeichnis
        return (prefix + path.lstrip("/") + "/index.html").replace("//", "/")

    if suffix:
        root, ext = os.path.splitext(path)
        path = root + suffix + ext
    return (prefix + path.lstrip("/")).replace("//", "/")


def web_path(url):
    """Wurzel-relativer Pfad, wie er im HTML stehen soll."""
    lp = local_path(url)
    if lp.endswith("/index.html"):
        return "/" + lp[: -len("index.html")]
    return "/" + lp


def fetch(url, tries=3):
    last = None
    for i in range(tries):
        try:
            sp = urllib.parse.urlsplit(url)
            safe = urllib.parse.urlunsplit((
                sp.scheme, sp.netloc,
                urllib.parse.quote(sp.path, safe="/%"),
                urllib.parse.quote(sp.query, safe="=&%"), ""))
            req = urllib.request.Request(safe, headers={
                "User-Agent": UA,
                "Accept": "*/*",
                "Accept-Encoding": "gzip",
                "Accept-Language": "de-CH,de;q=0.9",
            })
            with urllib.request.urlopen(req, timeout=45) as r:
                data = r.read()
                if r.headers.get("Content-Encoding") == "gzip":
                    try:
                        data = gzip.decompress(data)
                    except Exception:
                        pass
                ctype = (r.headers.get("Content-Type") or "").split(";")[0].strip().lower()
                return data, ctype, r.geturl()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(0.6 * (i + 1))
    raise last


# ---------------------------------------------------------------- URL-Extraktion

ATTR_RE = re.compile(
    r"""(?:href|src|data-src|data-original|data-bg|data-background|poster|data-thumb|data-large_image)\s*=\s*["']([^"']+)["']""",
    re.I)
SRCSET_RE = re.compile(r"""(?:srcset|data-srcset|imagesrcset)\s*=\s*["']([^"']+)["']""", re.I)
CSSURL_RE = re.compile(r"""url\(\s*['"]?([^'")]+?)['"]?\s*\)""", re.I)
IMPORT_RE = re.compile(r"""@import\s+(?:url\()?\s*['"]([^'"]+)['"]""", re.I)
ABS_RE = re.compile(r"""(?:https?:)?//(?:www\.)?bildstudio\.ch/[^\s"'<>)\\\]]*""", re.I)


def extract(data, ctype, url):
    """Gibt (asset_urls, page_urls) zurück."""
    try:
        text = data.decode("utf-8", "ignore")
    except Exception:  # noqa: BLE001
        return set(), set()

    found = set()

    if "html" in ctype:
        for m in ATTR_RE.finditer(text):
            found.add(m.group(1))
        for m in SRCSET_RE.finditer(text):
            for part in m.group(1).split(","):
                cand = part.strip().split()
                if cand:
                    found.add(cand[0])
        for m in CSSURL_RE.finditer(text):
            found.add(m.group(1))
        for m in ABS_RE.finditer(text):
            found.add(m.group(0))
    elif "css" in ctype:
        for m in CSSURL_RE.finditer(text):
            found.add(m.group(1))
        for m in IMPORT_RE.finditer(text):
            found.add(m.group(1))
    else:  # js / json
        for m in ABS_RE.finditer(text):
            found.add(m.group(0))
        for m in CSSURL_RE.finditer(text):
            found.add(m.group(1))

    assets, pgs = set(), set()
    for raw in found:
        u = norm(raw, url)
        if not u:
            continue
        path = urllib.parse.urlsplit(u).path
        ext = os.path.splitext(path)[1].lower()
        is_page = (urllib.parse.urlsplit(u).netloc.lower() == BASE_HOST
                   and (ext in ("", ".html", ".htm", "/"))
                   and "/wp-content/" not in path
                   and "/wp-includes/" not in path
                   and "/wp-json/" not in path
                   and not path.startswith("/wp-admin"))
        if is_page:
            pgs.add(u)
        else:
            assets.add(u)
    return assets, pgs


# ---------------------------------------------------------------- Download

work = queue.Queue()
counter = {"n": 0}


def save(url, data):
    lp = local_path(url)
    dest = os.path.join(OUT, lp)
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.isdir(dest):          # Kollision Datei/Verzeichnis
        dest = os.path.join(dest, "index.html")
    with open(dest, "wb") as f:
        f.write(data)
    return lp


def worker():
    while True:
        try:
            url = work.get(timeout=2)
        except queue.Empty:
            return
        try:
            data, ctype, final = fetch(url)
            lp = save(url, data)
            with lock:
                saved[url] = lp
                counter["n"] += 1
                n = counter["n"]
                if "html" in ctype:
                    pages.add(url)
            if n % 25 == 0:
                print("  ... %d Dateien" % n, flush=True)

            if ctype and ("html" in ctype or "css" in ctype
                          or "javascript" in ctype or "json" in ctype):
                assets, pgs = extract(data, ctype, final or url)
                with lock:
                    new = [u for u in (assets | pgs) if u not in seen_urls]
                    for u in new:
                        seen_urls.add(u)
                for u in new:
                    work.put(u)
        except Exception as e:  # noqa: BLE001
            with lock:
                failed[url] = str(e)[:160]
        finally:
            work.task_done()


def main():
    seeds = [BASE + "/"]
    # Sitemaps auswerten
    for sm in ["/wp-sitemap.xml", "/wp-sitemap-posts-page-1.xml",
               "/wp-sitemap-posts-bauman_portfolio-1.xml",
               "/wp-sitemap-taxonomies-portfolio_category-1.xml"]:
        try:
            data, _, _ = fetch(BASE + sm)
            for loc in re.findall(rb"<loc>([^<]+)</loc>", data):
                u = norm(loc.decode("utf-8", "ignore"))
                if u and not u.endswith(".xml"):
                    seeds.append(u)
        except Exception:  # noqa: BLE001
            pass

    for u in seeds:
        u = norm(u)
        if u and u not in seen_urls:
            seen_urls.add(u)
            work.put(u)

    print("Start mit %d Seiten aus Sitemap." % len(seen_urls), flush=True)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    print("\nFertig: %d Dateien gespeichert, %d Fehler." % (len(saved), len(failed)))
    meta = {"saved": saved, "failed": failed, "pages": sorted(pages)}
    with open(os.path.join(os.path.dirname(OUT), "tools", "mirror-report.json"), "w") as f:
        json.dump(meta, f, indent=1, ensure_ascii=False)
    if failed:
        print("\nFehlgeschlagen:")
        for u, e in list(failed.items())[:30]:
            print("  %s -> %s" % (u, e))


if __name__ == "__main__":
    main()
