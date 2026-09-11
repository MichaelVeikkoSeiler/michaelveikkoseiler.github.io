# bildstudio.ch — statischer Nachbau

**Live: https://michaelveikkoseiler.github.io**

Die bisherige WordPress-Seite (Theme «Bauman») als statische Website. Kein PHP,
keine Datenbank, kein WordPress — nur HTML, CSS, JS und Bilder. Damit läuft die
Seite gratis auf GitHub Pages und braucht keinen bezahlten Anbieter mehr.

**Design ist unverändert übernommen.** Layoutmasse, Schriften, Animationen und
Bilder stammen 1:1 aus der Live-Seite.

## Inhalt

```
docs/            die fertige Website — genau dieser Ordner geht ins Netz
  index.html     Startseite
  404.html       Fehlerseite (im Seitendesign)
  .nojekyll      schaltet Jekyll ab (siehe unten, wichtig)
  _headers       Caching-Regeln — nur für einen späteren Wechsel zu Cloudflare
  wp-content/    Bilder, Videos, Theme-CSS/JS (Pfade wie im Original belassen)
  _ext/          lokal abgelegte Schriften: Poppins, Oswald, Font Awesome
tools/           Skripte, mit denen der Nachbau erzeugt wurde
  mirror.py      lädt die Live-Seite herunter
  rewrite.py     schreibt absolute URLs auf relative Pfade um
  cleanup.py     entfernt tote WordPress-Reste
  fix_fonts.py   trennt die beiden Google-Fonts-Stylesheets
  check.py       prüft, ob jede referenzierte Datei existiert
  difftext.py    vergleicht den sichtbaren Text mit der alten Live-Seite
  serve.js       lokaler Vorschau-Server
```

Umfang: 39 Seiten, 478 Dateien, rund 83 MB (davon 76 MB Bilder und Videos).

### Warum heisst der Ordner `docs`?

GitHub Pages kann nur zwei Orte ausliefern: das Wurzelverzeichnis oder einen
Ordner namens `docs`. Ein frei gewählter Name ist nicht möglich. Da neben der
Website auch die Skripte im Repository liegen, die niemand im Netz sehen soll,
fiel die Wahl auf `docs`.

### Wozu `.nojekyll`?

GitHub Pages schickt jede Seite standardmässig durch Jekyll, und Jekyll
**ignoriert alle Ordner mit führendem Unterstrich**. Ohne diese leere Datei
würde `_ext/` verschwinden — und damit sämtliche Schriften.

## Lokal ansehen

```bash
node tools/serve.js
```

Dann `http://localhost:8765` im Browser öffnen. Der Server verhält sich wie
GitHub Pages: `/kontakt/` liefert `kontakt/index.html`, Unbekanntes die
404-Seite.

## Veröffentlichen

Jeder Push auf `main` veröffentlicht automatisch:

```bash
git add -A
git commit -m "Beschreibung der Änderung"
git push
```

Nach ein bis zwei Minuten ist die neue Fassung im Netz. Den Fortschritt zeigt
GitHub im Reiter **Actions**.

### Einrichtung (erledigt)

**Settings → Pages**: Source `Deploy from a branch`, Branch `main`, Ordner
`/docs`. Das Repository heisst `michaelveikkoseiler.github.io` und ist
öffentlich — beides Voraussetzung: Nur ein so benanntes Repository wird auf der
obersten Ebene ausgeliefert (sonst lägen alle Pfade eine Ebene daneben), und
GitHub Pages ist bei privaten Repositories kostenpflichtig.

### Eigene Domain

**Achtung, hier steckt eine Falle.** Der MX-Eintrag von bildstudio.ch zeigt nicht
auf einen eigenen Mailserver-Namen, sondern auf die Domain selbst:

```
MX   bildstudio.ch  ->  bildstudio.ch
A    bildstudio.ch  ->  149.126.4.71   (cyon)
```

Wer also den A-Eintrag der Hauptdomain auf die GitHub-IPs umbiegt, leitet damit
auch die gesamte eingehende Post an GitHub um - und die ist dann verloren, nicht
nur verzoegert. Die uebliche GitHub-Anleitung mit vier A-Eintraegen auf `@` ist
fuer diese Domain daher **falsch**.

**Sicherer Weg (umgesetzt):** nur `www` umziehen, Hauptdomain bei cyon lassen.

| Typ | Name | Ziel | |
|---|---|---|---|
| CNAME | `www` | `michaelveikkoseiler.github.io` | geaendert |
| A | `@` | `149.126.4.71` | **unveraendert lassen** |
| MX | `@` | `bildstudio.ch` | **unveraendert lassen** |
| TXT | `@` | `v=spf1 ...` | **unveraendert lassen** |

`bildstudio.ch` ohne www leitet weiterhin ueber cyon auf `www.bildstudio.ch`
weiter und landet damit auf der neuen Seite. Beide Adressen funktionieren.

Auf GitHub-Seite genuegt die Datei `docs/CNAME` mit dem Inhalt
`www.bildstudio.ch` - GitHub Pages liest sie und stellt das Zertifikat selbst
aus. Danach unter **Settings -> Pages** *Enforce HTTPS* ankreuzen, sobald die
Option anwaehlbar wird (kann bis zu einer Stunde dauern).

**Spaeter, wenn das Postfach geklaert ist:** Soll auch die Hauptdomain direkt zu
GitHub, braucht der Mailversand vorher einen eigenen Hostnamen - etwa
`mail.bildstudio.ch` mit A-Eintrag auf cyons IP und MX darauf zeigend. Diesen
Hostnamen bei cyon erfragen statt raten. Erst danach duerfen die A-Eintraege
von `@` auf die GitHub-IPs (185.199.108-111.153) wechseln.

## Bekannte Punkte

* **Abweichungen zur alten Seite (bewusst):** Mailadresse überall auf
  `veikko@gmx.ch` gesetzt (die alte Seite verlinkte `info@bildstudio.ch`, zeigte
  aber `veikko@gmx.ch` an), Copyright auf 2026 aktualisiert.
* **Tippfehler auf `/portrait/` korrigiert** (standen so auf der alten Seite):
  «Parter» → «Partner», «Anfangs 2019» → «Anfang 2019». `difftext.py` meldet
  diese Stellen deshalb als Abweichung — das ist gewollt.
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
* **Traffic-Limit:** GitHub Pages nennt 100 GB pro Monat. Eine Startseite lädt
  rund 15 MB — das reicht für etwa 6000 Besuche monatlich.

## Neu erzeugen

Solange die alte Seite noch online ist, lässt sich der ganze Vorgang wiederholen:

```bash
python3 tools/mirror.py && python3 tools/rewrite.py && python3 tools/cleanup.py && python3 tools/fix_fonts.py && python3 tools/check.py
```

`check.py` meldet am Ende, ob alle internen Verweise auflösen.

Danach `python3 tools/difftext.py` laufen lassen: Es vergleicht den sichtbaren
Text jeder Seite mit dem der alten Live-Seite. `rewrite.py` trifft beim
Umschreiben der URLs gelegentlich auch Text, der für Leser bestimmt ist — so
wurde aus «Webseite: https://www.bildstudio.ch/» im Impressum einmal
«Webseite: /index.html». Solche Treffer fallen sonst niemandem auf.
