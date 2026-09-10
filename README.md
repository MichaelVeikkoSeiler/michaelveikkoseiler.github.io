# bildstudio.ch — statischer Nachbau

Die bisherige WordPress-Seite (Theme «Bauman») als statische Website. Kein PHP,
keine Datenbank, kein WordPress — nur HTML, CSS, JS und Bilder. Damit läuft die
Seite auf jedem Gratis-Hosting und braucht keinen bezahlten Anbieter mehr.

**Design ist unverändert übernommen.** Layoutmasse, Schriften, Animationen und
Bilder stammen 1:1 aus der Live-Seite.

## Inhalt

```
site/            die fertige Website — genau dieser Ordner wird hochgeladen
  index.html     Startseite
  404.html       Fehlerseite (im Seitendesign)
  _headers       Caching- und Sicherheits-Header für Cloudflare Pages
  wp-content/    Bilder, Videos, Theme-CSS/JS (Pfade wie im Original belassen)
  _ext/          lokal abgelegte Schriften: Poppins, Oswald, Font Awesome
tools/           Skripte, mit denen der Nachbau erzeugt wurde
  mirror.py      lädt die Live-Seite herunter
  rewrite.py     schreibt absolute URLs auf relative Pfade um
  cleanup.py     entfernt tote WordPress-Reste
  fix_fonts.py   trennt die beiden Google-Fonts-Stylesheets
  check.py       prüft, ob jede referenzierte Datei existiert
  serve.js       lokaler Vorschau-Server
```

Umfang: 39 Seiten, 477 Dateien, rund 83 MB (davon 76 MB Bilder und Videos).

## Lokal ansehen

```bash
node tools/serve.js
```

Dann `http://localhost:8765` im Browser öffnen. Der Server verhält sich wie
Cloudflare Pages: `/kontakt/` liefert `kontakt/index.html`, Unbekanntes die
404-Seite.

## Veröffentlichen auf Cloudflare Pages

Der direkte Upload ist der kürzeste Weg — dafür wird kein GitHub-Konto und kein
Git-Repository gebraucht.

```bash
npx wrangler pages deploy site --project-name=bildstudio
```

Beim ersten Aufruf öffnet sich der Browser zur Anmeldung bei Cloudflare. Danach
liegt die Seite unter `bildstudio.pages.dev`.

Eigene Domain verbinden: im Cloudflare-Dashboard unter
**Workers & Pages → bildstudio → Custom domains** sowohl `bildstudio.ch` als auch
`www.bildstudio.ch` hinzufügen. Cloudflare legt die DNS-Einträge und das
TLS-Zertifikat selbst an.

Für jede spätere Änderung genügt derselbe Befehl erneut.

### Grenzwerte (alle deutlich unterschritten)

| | Limit | Diese Seite |
|---|---|---|
| Dateien pro Deployment | 20 000 | 477 |
| Grösse pro Datei | 25 MB | 5,3 MB |
| Traffic | unbegrenzt | — |

## Bekannte Punkte

* **Mailadresse auf `/kontakt/`:** Der Link zeigt `veikko@gmx.ch` an, führt aber
  auf `mailto:info@bildstudio.ch`. Das war schon auf der alten Seite so. Falls
  das Postfach `info@bildstudio.ch` beim bisherigen Anbieter liegt und mit dem
  Hosting wegfällt, sollte der Link auf die Gmx-Adresse zeigen —
  in `site/kontakt/index.html`.
* **Cookie-Banner:** Ist übernommen, obwohl die Seite gar kein Tracking
  einsetzt (kein Google Analytics, keine Pixel). Er könnte ersatzlos entfallen.
* **Ladezeit:** Der Preloader wartet, bis alle Kopfbilder geladen sind — das
  dauert. Die Bilder sind unkomprimierte JPEGs direkt aus WordPress.
  Optimierung würde die 76 MB grob halbieren, ohne sichtbaren Qualitätsverlust.
* **Doppelte Adressen:** Jede Portfolio-Seite ist unter `/fotografie/` und unter
  `/bauman_portfolio/fotografie/` erreichbar. So war es auch im Original; die
  Navigation nutzt durchgehend die kurze Form.
* **Nicht funktionsfähig ohne WordPress:** die Suche (war nur auf
  `/geschichten/` eingebunden) und Kommentare. Beides wurde entfernt.
  Ein Kontaktformular gab es auf der Seite nicht.

## Neu erzeugen

Solange die alte Seite noch online ist, lässt sich der ganze Vorgang wiederholen:

```bash
python3 tools/mirror.py && python3 tools/rewrite.py && python3 tools/cleanup.py && python3 tools/fix_fonts.py && python3 tools/check.py
```

`check.py` meldet am Ende, ob alle internen Verweise auflösen.
