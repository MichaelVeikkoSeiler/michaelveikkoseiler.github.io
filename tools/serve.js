// Minimaler statischer Server für die lokale Vorschau der gespiegelten Seite.
// Verhält sich wie Cloudflare Pages: /pfad/ -> /pfad/index.html, sonst 404.html
const http = require("http");
const fs = require("fs");
const path = require("path");

const ROOT = path.resolve(__dirname, "..", "docs");
const PORT = Number(process.env.PORT || 8765);

const TYPES = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "application/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".xml": "application/xml; charset=utf-8",
  ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
  ".gif": "image/gif", ".svg": "image/svg+xml", ".webp": "image/webp",
  ".ico": "image/x-icon", ".mp4": "video/mp4", ".webm": "video/webm",
  ".woff": "font/woff", ".woff2": "font/woff2", ".ttf": "font/ttf",
  ".eot": "application/vnd.ms-fontobject", ".otf": "font/otf",
  ".txt": "text/plain; charset=utf-8",
};

function send(res, code, body, type) {
  res.writeHead(code, { "Content-Type": type || "text/plain; charset=utf-8" });
  res.end(body);
}

http.createServer((req, res) => {
  let urlPath;
  try {
    urlPath = decodeURIComponent(new URL(req.url, "http://x").pathname);
  } catch {
    return send(res, 400, "Bad request");
  }

  let file = path.normalize(path.join(ROOT, urlPath));
  if (!file.startsWith(ROOT)) return send(res, 403, "Forbidden");

  // Verzeichnis -> index.html; extensionslos -> Redirect auf /pfad/
  if (fs.existsSync(file) && fs.statSync(file).isDirectory()) {
    if (!urlPath.endsWith("/")) {
      res.writeHead(301, { Location: urlPath + "/" });
      return res.end();
    }
    file = path.join(file, "index.html");
  }

  if (!fs.existsSync(file)) {
    const fallback = path.join(ROOT, "404.html");
    if (fs.existsSync(fallback)) {
      return send(res, 404, fs.readFileSync(fallback), TYPES[".html"]);
    }
    return send(res, 404, "404 – " + urlPath);
  }

  const ext = path.extname(file).toLowerCase();
  send(res, 200, fs.readFileSync(file), TYPES[ext] || "application/octet-stream");
}).listen(PORT, () => {
  console.log("Vorschau läuft auf http://localhost:" + PORT + "/  (Wurzel: " + ROOT + ")");
});
