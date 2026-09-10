# bildstudio.ch — statischer Nachbau

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

### Einmalige Einrichtung

Unter **Settings → Pages**: Source `Deploy from a branch`, Branch `main`,
Ordner `/docs`. Das Repository muss dafür öffentlich sein — GitHub Pages ist bei
privaten Repositories kostenpflichtig.

### Eigene Domain

Unter **Settings → Pages → Custom domain** `www.bildstudio.ch` eintragen. Dann
beim Domain-Anbieter (aktuell cyon) die DNS-Einträge setzen:

| Typ | Name | Ziel |
|---|---|---|
| CNAME | `www` | `michaelveikkoseiler.github.io` |
| A | `@` | `185.199.108.153` |
| A | `@` | `185.199.109.153` |
| A | `@` | `185.199.110.153` |
| A | `@` | `185.199.111.153` |

Anschliessend in GitHub **Enforce HTTPS** ankreuzen — das Zertifikat stellt
GitHub selbst aus.

> **Achtung Mail:** Der MX-Eintrag von bildstudio.ch zeigt auf denselben Server
> wie die Website (cyon, 149.126.4.71). Wer die A-Einträge ändert, darf die
> MX-Einträge nicht anfassen, sonst fällt `info@bildstudio.ch` aus. Und solange
> das Postfach bei cyon liegt, kann das Hosting dort nicht vollständig gekündigt
> werden.

## Bekannte Punkte

* **Mailadresse auf `/kontakt/`:** Der Link zeigt `veikko@gmx.ch` an, führt aber
  auf `mailto:info@bildstudio.ch`. Das war schon auf der alten Seite so — zu
  ändern in `docs/kontakt/index.html`.
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
