#!/usr/bin/env node
// Store-Bilder montieren: Rohaufnahme der App + Beschriftung auf ruhigem Grund.
//
// Richtlinie 2.3.3 erlaubt «text and image overlays» ausdrücklich; verlangt ist,
// dass das Fenster die eingereichte Fassung in Benutzung zeigt. Die Rohaufnahmen
// kommen deshalb aus der gebauten Store-App (Umschalt-Befehl-Vier, dann Leertaste
// auf das Fenster) und NICHT aus dem Browser — dort rendert die Oberfläche den
// Zweig für den Direktvertrieb (Knopf «Releases»), den die Store-Fassung ausblendet.
//
// Gestaltung, Masse und Texte: appstore/texte/bildtexte.md und bildtexte.json.
// Schrift: Recursive aus site/fonts (SIL OFL 1.1, Lizenztext in fonts/OFL.txt) —
// dieselbe wie auf der Website.
//
// Aufruf: node scripts/appstore-montage.mjs [--sprachen de,en] [--quelle appstore/upload]
//                                           [--ziel appstore/store]
import fs from "node:fs";
import http from "node:http";
import path from "node:path";
import { createRequire } from "node:module";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(ROOT, "frontend/package.json"));
const { webkit } = require("playwright");

const arg = (name, std) => { const i = process.argv.indexOf(`--${name}`); return i > 0 ? process.argv[i + 1] : std; };
const SPRACHEN = arg("sprachen", "de,en,fr,it").split(",");
const QUELLE = path.join(ROOT, arg("quelle", "appstore/upload"));
const ZIEL = path.join(ROOT, arg("ziel", "appstore/store"));
const DATEN = JSON.parse(fs.readFileSync(path.join(ROOT, "appstore/texte/bildtexte.json"), "utf8"));

// Apple, Mac: 16:10. Wir liefern die grösste Fassung, Apple skaliert herunter.
const B = 2880, H = 1800;
const RAND = 140;          // Aussenrand
const FENSTER_B = B - 2 * RAND;

const TYPEN = { ".png": "image/png", ".woff2": "font/woff2", ".html": "text/html; charset=utf-8" };
const server = http.createServer((req, res) => {
  const rel = decodeURIComponent(req.url.split("?")[0]).replace(/^\/+/, "");
  const datei = path.join(ROOT, rel);
  if (!datei.startsWith(ROOT)) { res.writeHead(403).end(); return; }
  fs.readFile(datei, (err, buf) => {
    if (err) { res.writeHead(404).end(); return; }
    res.writeHead(200, { "content-type": TYPEN[path.extname(datei)] || "application/octet-stream" });
    res.end(buf);
  });
});
await new Promise((ok) => server.listen(0, "127.0.0.1", ok));
const BASIS = `http://127.0.0.1:${server.address().port}/`;

const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
/** Zeilenumbrüche der Schlagzeile stehen in den Texten als \n. */
const zeilen = (s) => esc(s).split("\n").join("<br>");

function seite(bild, titel, unter, dunkel) {
  const grund = dunkel ? "#1a1d20" : "#f3f5f6";
  const tinte = dunkel ? "#ffffff" : "#000000";
  const leise = dunkel ? "rgba(255,255,255,.72)" : "rgba(0,0,0,.70)";
  const schatten = dunkel ? "0 24px 70px rgba(0,0,0,.55)" : "0 24px 60px rgba(0,0,0,.18)";
  const rahmen = dunkel ? "rgba(255,255,255,.14)" : "rgba(0,0,0,.10)";
  return `<!doctype html><meta charset="utf-8"><style>
  @font-face { font-family:"Recursive"; src:url("${BASIS}site/fonts/Recursive_VF.woff2") format("woff2");
               font-weight:300 1000; font-display:block; }
  * { margin:0; padding:0; box-sizing:border-box; }
  html, body { width:${B}px; height:${H}px; overflow:hidden; }
  body { background:${grund}; color:${tinte};
         font-family:"Recursive", system-ui, sans-serif;
         font-variation-settings:'CASL' 0, 'MONO' 0;
         -webkit-font-smoothing:antialiased; }
  .blatt { padding:${RAND}px ${RAND}px 0; }
  /* Feine Linie in der Akzentfarbe: der einzige Schmuck. */
  .strich { width:120px; height:4px; background:#4f46e5; border-radius:2px; margin-bottom:34px; }
  h1 { font-size:96px; line-height:1.12; font-weight:640; letter-spacing:-.015em; }
  p { font-size:44px; line-height:1.32; font-weight:400; color:${leise}; margin-top:20px;
      max-width:2100px; }
  /* Das Fenster läuft unten aus dem Bild — so bleibt die Oberfläche gross lesbar. */
  .fenster { margin-top:72px; width:${FENSTER_B}px; border-radius:18px; overflow:hidden;
             box-shadow:${schatten}; outline:1px solid ${rahmen}; outline-offset:-1px; }
  .fenster img { display:block; width:100%; }
  </style>
  <div class="blatt">
    <div class="strich"></div>
    <h1>${zeilen(titel)}</h1>
    <p>${esc(unter)}</p>
    <div class="fenster"><img src="${BASIS}${bild}"></div>
  </div>`;
}

const browser = await webkit.launch();
let zahl = 0;
for (const sprache of SPRACHEN) {
  const ordner = path.join(ZIEL, sprache);
  fs.mkdirSync(ordner, { recursive: true });
  let nr = 0;
  for (const eintrag of DATEN.bilder) {
    nr += 1;
    const quelle = path.join(QUELLE, sprache, eintrag.quelle);
    if (!fs.existsSync(quelle)) { console.log(`… fehlt, übersprungen: ${path.relative(ROOT, quelle)}`); continue; }
    const text = eintrag[sprache];
    if (!text) { console.error(`ABBRUCH: kein Text für ${sprache} in ${eintrag.quelle}`); process.exit(1); }
    const page = await browser.newPage({ viewport: { width: B, height: H }, deviceScaleFactor: 1 });
    await page.setContent(seite(path.relative(ROOT, quelle), text.titel, text.unter, eintrag.grund === "dunkel"),
                          { waitUntil: "networkidle" });
    await page.evaluate(() => document.fonts.ready);
    // Die Rohaufnahme trägt schon eine Nummer; hier zählt die Reihenfolge im Store.
    const motiv = eintrag.quelle.replace(/^\d+-/, "");
    const datei = path.join(ordner, `${String(nr).padStart(2, "0")}-${motiv}`);
    await page.screenshot({ path: datei });
    await page.close();
    zahl += 1;
  }
  console.log(`✓ ${sprache}: ${nr} Motive → ${path.relative(ROOT, ordner)}`);
}
await browser.close();
server.close();
console.log(`${zahl} Bilder montiert (${B}×${H}).`);
