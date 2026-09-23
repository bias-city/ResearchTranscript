#!/usr/bin/env node
// App-Store-Screenshots: 7 Motive × 4 Sprachen × hell/dunkel × 4 Grössen.
//
// Aufgenommen wird die echte Oberfläche (frontend/dist) im Browser-Betrieb
// gegen ein Demo-Backend (uvicorn, Kind-Motor) mit dem ERFUNDENEN Interview
// aus docs/demo — nie echtes Forschungsmaterial. Playwright-WebKit, weil die
// App in WKWebView läuft (gleiche Schrift- und Formulardarstellung).
//
// Ablauf: Backend starten → Demo transkribieren (≈ 30 s, whisper-cli/ffmpeg
// aus Homebrew, argmax-cli + SpeakerKit-Modelle aus dem Haupt-Checkout) →
// Sprecher benennen, zwei weitere Einträge importieren → je Sprache, Modus
// und Grösse die Motive aufnehmen. Pfade in den Einstellungen werden im DOM
// neutralisiert (/Users/nora/…).
//
// Grössen (Apple, Mac, 16:10): 1280×800, 1440×900, 2560×1600, 2880×1800.
// Ausgabe: appstore/screenshots/<sprache>/<hell|dunkel>/<BxH>/NN-motiv.png
//
// Aufruf: node scripts/appstore-screenshots.mjs [--nur de] [--schnell] [--hilfe]
//   --schnell: nur 2880×1800
//   --hilfe:   Bilder fürs Handbuch (modules/HilfeModule) statt für den Store:
//              frontend/public/hilfe/<sprache>/<hell|dunkel>/NN-motiv.jpg,
//              1440×912 (Fenster 1200×760 × 1,2 — das Handbuch zeigt sie
//              höchstens 716 px breit, das reicht für Retina), JPEG, dazu
//              drei Motive nur fürs Handbuch (Memo, Steuerzeile, Zeile).
//              Danach `npm run build`, damit sie in dist landen.
//   --satz:    der KURATIERTE Store-Satz statt aller Motive: Transkript, Edit,
//              Memo, Export in einem breiten Fenster (1440×720 × 2 = 2880×1440,
//              füllt die Bühne der Montage) und in beiden Erscheinungsbildern.
//              Die Montage nimmt je Motiv das hier erzeugte Bild und greift nur
//              dort auf Handaufnahmen in appstore/upload/ zurück, wo ein Motiv
//              im Browser-Betrieb nicht entstehen kann.
//   --site:    Bilder für die Website: site/img/<motiv>-<sprache>.png, 1200×750,
//              nur hell. Startet scripts/demo_backend.py (erfundene Zotero-
//              Einträge) und transkribiert zusätzlich ein erzeugtes Demo-Video
//              (ffmpeg, Farbverlauf + Ton des Demo-Interviews).
import { spawn } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(ROOT, "frontend/package.json"));
const { webkit } = require("playwright");

const PORT = 5631;
const B = `http://127.0.0.1:${PORT}`;
const HILFE = process.argv.includes("--hilfe");
const SATZ = process.argv.includes("--satz");
const SITE = process.argv.includes("--site");
const AUS = SITE ? path.join(ROOT, "site/img") : HILFE ? path.join(ROOT, "frontend/public/hilfe") : path.join(ROOT, "appstore/screenshots");
const SCRATCH = fs.mkdtempSync(path.join(os.tmpdir(), "rt-shots-"));
const LIB = path.join(SCRATCH, "lib");
const DEMO = path.join(ROOT, "docs/demo/housing-cooperatives-interview.mp3");
const HAUPT = path.resolve(ROOT, "../enrich-transcript");   // argmax-cli + models/speakerkit
const arg = (n) => { const i = process.argv.indexOf(n); return i >= 0 ? process.argv[i + 1] ?? true : null; };
const SPRACHEN = arg("--nur") ? [arg("--nur")] : ["de", "en", "fr", "it"];
const GROESSEN = SITE ? [[1200, 750, 1]] : HILFE ? [[1200, 760, 1.2]] : SATZ ? [[1440, 720, 2]] : (arg("--schnell") ? [[1440, 900, 2]] : [[1280, 800, 1], [1440, 900, 1], [1280, 800, 2], [1440, 900, 2]]);
const MODI = SITE ? [["hell", "light"]] : [["hell", "light"], ["dunkel", "dark"]];

const warte = (ms) => new Promise((r) => setTimeout(r, ms));
async function api(pfad, init) {
  const r = await fetch(B + pfad, init);
  if (!r.ok) throw new Error(`${pfad}: ${r.status} ${await r.text()}`);
  return r;
}
const json = (body, method = "POST") => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

// ---------- Backend ----------
fs.mkdirSync(LIB, { recursive: true });
fs.mkdirSync(path.join(SCRATCH, "cfg"), { recursive: true });
fs.writeFileSync(path.join(SCRATCH, "cfg/config.json"), JSON.stringify({ library_root: LIB, zotero_consent: SITE }));
const server = spawn("uv", ["run", "uvicorn", ...(SITE ? ["demo_backend:app", "--app-dir", path.join(ROOT, "scripts")] : ["researchtranscript.main:app"]), "--port", String(PORT)], {
  cwd: path.join(ROOT, "backend"),
  env: { ...process.env, LT_SERVE_PORT: String(PORT), LT_CONFIG_DIR: path.join(SCRATCH, "cfg"),
         LT_MODELS_DIR: path.join(ROOT, "frontend/src-tauri/resources/models"), LT_APP_ROOT: HAUPT, LT_MOTOR: "kind", DEMO_ZOTERO_DIR: path.join(SCRATCH, "Zotero") },
  stdio: ["ignore", "ignore", "inherit"],
});
const ende = () => { try { server.kill(); } catch { /* schon weg */ } };
process.on("exit", ende); process.on("SIGINT", () => { ende(); process.exit(1); });

for (let i = 0; i < 60; i++) { try { await api("/api/health"); break; } catch { await warte(500); } }
console.log("Backend bereit");

// ---------- Demo-Material ----------
const { job_id } = await (await api("/api/transcribe-path", json({ path: DEMO, language: "en", speaker_range: "2-2" }))).json();
let job;
for (let i = 0; i < 400; i++) {
  job = await (await api(`/api/jobs/${job_id}`)).json();
  if (["completed", "failed", "cancelled"].includes(job.status)) break;
  await warte(500);
}
if (job.status !== "completed") throw new Error(`Demo-Transkription: ${job.status} ${job.error ?? ""}`);
let eid = job.eintrag;
let t = await (await api(`/api/transcripts/${eid}`)).json();
// erste Stimme = Nora (Interviewerin), zweite = Julian
const erste = t.segmente[0].sprecher;
t.sprecher = t.sprecher.map((s) => ({ id: s.id, name: s.id === erste ? "Nora" : "Julian" }));
// zwei Memos, damit Icon-Punkt und Marker in der Wellenform zu sehen sind
const MEMOS = { 7: "Key tension: speed vs. participation — compare with interview 02.", 15: "Nine months on the kitchen: follow up on how the decision was finally taken." };
await api(`/api/transcripts/${eid}`, json({ sprecher: t.sprecher, segmente: t.segmente.map(({ id, start, end, sprecher, text }, i) => ({ id, start, end, sprecher, text, memo: MEMOS[i] ?? null })) }, "PUT"));
await api(`/api/transcripts/${eid}/rename`, json({ name: "Interview_01_Julian" }));
const vtt = await (await api(`/api/transcripts/${eid}/export/vtt`)).arrayBuffer();
for (const name of ["Interview_02_Mara", "Interview_03_Workshop"]) {
  const fd = new FormData();
  fd.append("datei", new Blob([vtt], { type: "text/vtt" }), `${name}.vtt`);
  fd.append("audio", new Blob([fs.readFileSync(DEMO)], { type: "audio/mpeg" }), `${name}.mp3`);
  await api("/api/import", { method: "POST", body: fd });
}
// Website: ein Eintrag mit Video — erzeugter Farbverlauf, Ton des Demo-Interviews
let videoEid = null;
if (SITE) {
  const { execFileSync } = await import("node:child_process");
  const mp4 = path.join(SCRATCH, "Gruppengespraech_Quartier.mp4");
  execFileSync("ffmpeg", ["-v", "error", "-y", "-f", "lavfi", "-i", "gradients=s=640x360:c0=0x7400a4:c1=0x151515:speed=0.008",
    "-i", DEMO, "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", "25", "-c:a", "aac", mp4]);
  const v = await (await api("/api/transcribe-path", json({ path: mp4, language: "en", speaker_range: "2-2" }))).json();
  let vj;
  for (let i = 0; i < 400; i++) { vj = await (await api(`/api/jobs/${v.job_id}`)).json(); if (["completed", "failed", "cancelled"].includes(vj.status)) break; await warte(500); }
  if (vj.status !== "completed") throw new Error(`Demo-Video: ${vj.status} ${vj.error ?? ""}`);
  videoEid = vj.eintrag;
  const vt = await (await api(`/api/transcripts/${videoEid}`)).json();
  const e1 = vt.segmente[0].sprecher;
  await api(`/api/transcripts/${videoEid}`, json({ sprecher: vt.sprecher.map((s) => ({ id: s.id, name: s.id === e1 ? "Nora" : "Julian" })),
    segmente: vt.segmente.map(({ id, start, end, sprecher, text }) => ({ id, start, end, sprecher, text })) }, "PUT"));
  await api(`/api/transcripts/${videoEid}/rename`, json({ name: "Gruppengespraech_Quartier" }));
}
const liste = (await (await api("/api/transcripts")).json()).transcripts;
eid = liste.find((e) => e.name === "Interview_01_Julian").id;
if (SITE) videoEid = liste.find((e) => e.name === "Gruppengespraech_Quartier").id;
// Wellenform-Cache vorab bauen
await api(`/api/transcripts/${eid}/wellenform?t0=0&t1=0&buckets=1`);
console.log(`Demo bereit: ${liste.length} Einträge, Editor-Eintrag ${eid}, ${t.segmente.length} Segmente`);

// ---------- Aufnahme ----------
const NEUTRAL = [
  [LIB, "/Users/nora/Documents/ResearchTranscript"],
  [path.join(ROOT, "frontend/src-tauri/resources/models"), "/Applications/ResearchTranscript.app/Contents/Resources/models"],
  [SCRATCH, "/Users/nora"], [os.homedir(), "/Users/nora"],
];
async function neutralisiere(page) {
  await page.evaluate((paare) => {
    const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      for (const [von, nach] of paare) if (n.nodeValue.includes(von)) n.nodeValue = n.nodeValue.split(von).join(nach);
    }
    for (const el of document.querySelectorAll("input")) {
      for (const [von, nach] of paare) if (el.value.includes(von)) el.value = el.value.split(von).join(nach);
    }
  }, NEUTRAL);
}

const browser = await webkit.launch();
let zahl = 0;
// Der Store-Satz zeigt die Maschine BEI DER ARBEIT. Dafür braucht es einen Lauf,
// der lange genug dauert, um alle Sprachen und beide Erscheinungsbilder
// aufzunehmen — sonst steht im Bild ein fertiger oder abgebrochener Auftrag.
// Deshalb: das Demo-Interview viermal hintereinander (acht Minuten Ton) und ein
// Lauf, der bei Bedarf erneuert wird. Abgebrochen wird erst ganz am Schluss.
let satzLauf = null, satzQuelle = null;
if (SATZ || SITE) {
  const { execFileSync } = await import("node:child_process");
  const lang = path.join(SCRATCH, "Interview_06_Baugruppe.mp3");
  // Acht bzw. sechzehn Minuten Ton: der Lauf muss alle Aufnahmen überdauern,
  // sonst steht in einem Bild «Fertig» statt eines arbeitenden Auftrags — und
  // für die Website darf er auch keinen zusätzlichen Bibliothekseintrag anlegen.
  execFileSync("ffmpeg", ["-v", "error", "-y", "-stream_loop", SITE ? "7" : "3", "-i", DEMO, "-c", "copy", lang]);
  satzQuelle = lang;
}
async function laufHalten() {
  if (satzLauf) {
    const stand = await (await api(`/api/jobs/${satzLauf}`)).json();
    if (!["completed", "failed", "cancelled"].includes(stand.status) && stand.progress < 85) return;
  }
  const r = await (await api("/api/transcribe-path", json({ path: satzQuelle, language: "en", speaker_range: "2-2" }))).json();
  satzLauf = r.job_id;
  for (let i = 0; i < 240; i++) {
    const stand = await (await api(`/api/jobs/${satzLauf}`)).json();
    if (stand.progress >= 30 || ["completed", "failed", "cancelled"].includes(stand.status)) break;
    await warte(500);
  }
}

// Memos im Bild sind Nutzertext — sie stehen in der Sprache der Oberfläche.
const MEMO_TEXTE = {
  de: { 7: "Kernspannung: Tempo gegen Beteiligung — mit Interview 02 vergleichen.",
        15: "Neun Monate für die Küche: nachfragen, wie die Entscheidung am Ende fiel." },
  en: { 7: "Key tension: speed vs. participation — compare with interview 02.",
        15: "Nine months on the kitchen: follow up on how the decision was finally taken." },
  fr: { 7: "Tension centrale : rythme contre participation — à comparer avec l'entretien 02.",
        15: "Neuf mois pour la cuisine : demander comment la décision a finalement été prise." },
  it: { 7: "Tensione centrale: ritmo contro partecipazione — da confrontare con l'intervista 02.",
        15: "Nove mesi per la cucina: chiedere come è stata presa la decisione." },
};
async function setzeMemos(sprache) {
  const texte = MEMO_TEXTE[sprache] ?? MEMO_TEXTE.en;
  const stand = await (await api(`/api/transcripts/${eid}`)).json();
  await api(`/api/transcripts/${eid}`, json({
    sprecher: stand.sprecher.map(({ id, name }) => ({ id, name })),
    segmente: stand.segmente.map(({ id, start, end, sprecher, text }, i) => ({ id, start, end, sprecher, text, memo: texte[i] ?? null })),
  }, "PUT"));
}

for (const sprache of SPRACHEN) {
  await api("/api/settings", json({ ui_language: sprache }));
  if (SATZ || SITE) await setzeMemos(sprache);
  for (const [modus, schema] of MODI) {
    for (const [b, h, dpr] of GROESSEN) {
      const ordner = SITE ? AUS : HILFE ? path.join(AUS, sprache, modus) : path.join(AUS, sprache, modus, `${b * dpr}x${h * dpr}`);
      fs.mkdirSync(ordner, { recursive: true });
      const ctx = await browser.newContext({ viewport: { width: b, height: h }, deviceScaleFactor: dpr, colorScheme: schema, locale: sprache });
      const page = await ctx.newPage();
      const oeffne = async (speicher) => {
        await page.goto(B + "/", { waitUntil: "networkidle" });
        await page.evaluate((s) => { localStorage.clear(); for (const [k, v] of Object.entries(s)) localStorage.setItem(k, v); }, speicher);
        await page.goto(B + "/", { waitUntil: "networkidle" });
        await warte(400);
      };
      // Store: PNG in voller Grösse · Handbuch: JPEG, optional nur ein Ausschnitt
      // Website: andere Dateinamen (<motiv>-<sprache>.png); Motive ohne Eintrag entfallen
      const SITE_NAMEN = { "01-editor.png": "hero", "02-ai-transkript.png": "batch", "03-bibliothek.png": "library",
        "04-suchen-ersetzen.png": "find", "05-sprecherfarbe.png": "edit", "06-export.png": "export", "07-einstellungen.png": "settings",
        "09-memo.png": "memo" };
      const knips = async (name, clip) => {
        if (SITE) {
          const motiv = SITE_NAMEN[name] ?? name.replace(/\.png$/, "");
          await page.screenshot({ path: path.join(ordner, `${motiv}-${sprache}.png`) });
          if (motiv === "library") fs.copyFileSync(path.join(ordner, `library-${sprache}.png`), path.join(ordner, `import-${sprache}.png`));
          zahl += 1; return;
        }
        const datei = path.join(ordner, HILFE ? name.replace(/\.png$/, ".jpg") : name);
        await page.screenshot(HILFE ? { path: datei, type: "jpeg", quality: 80, ...(clip ? { clip } : {}) } : { path: datei });
        zahl += 1;
      };
      const bild = async (name, clip) => {
        await page.mouse.move(b - 4, h / 2);          // kein Hover-Zustand im Bild
        await warte(150);
        await knips(name, clip);
      };
      const editor = { "lt.ui.tab": "editor", "lt.ui.editor": eid, [`lt.editor.aktiv.${eid}`]: "7", "lt.editor.schrift": "14" };

      // ---------- Kuratierter Store-Satz ----------
      // Vier Motive, die zusammen den Ablauf erzählen: du korrigierst, du
      // notierst, du exportierst, und die Maschine arbeitet. Welches Motiv im
      // Store hell und welches dunkel steht, entscheidet bildtexte.json — hier
      // entstehen beide Fassungen.
      if (SATZ) {
        // 01 Edit: eine Zeile OFFEN in Bearbeitung, Text markiert. Der Titel
        // verspricht das Korrigieren, also muss man es sehen.
        await oeffne({ ...editor, "lt.editor.seitentab": "sprecher" });
        await page.waitForSelector("[data-seg='7']");
        await warte(1200);                              // Wellenform + Höhenmessung
        const zeile = page.locator("[data-seg='7'] textarea.seg-text");
        await zeile.click();
        await zeile.evaluate((el) => {
          const ende = el.value.indexOf(" ", 46);
          el.setSelectionRange(14, ende > 0 ? ende : el.value.length);
        });
        await warte(300);
        await bild("01-editor.png");

        // 09 Memo: dieselbe Zeile, Dialog offen, Memo geschrieben
        await page.locator("[data-seg='7'] .lucide-notepad-text").first().click();
        await page.waitForSelector("[role='dialog'] textarea");
        await warte(400);
        await knips("09-memo.png");
        await page.keyboard.press("Escape");
        await warte(200);

        // 03 Export: offenes Menü mit allen Formaten
        await page.mouse.click(10, h - 10);
        await page.locator(".rt-SelectTrigger.rt-variant-soft").first().click();
        await warte(400);
        await knips("03-export.png");
        await page.keyboard.press("Escape");

        // 02 Transkript: ein Lauf ARBEITET — Blockzähler, Balken, mitlaufender
        // Text —, darüber wartet die Schlange. Der Lauf wird über die
        // Schnittstelle gestartet und danach abgebrochen, sonst legt jede
        // Sprache einen weiteren Eintrag an.
        await oeffne({ "lt.ui.tab": "ai" });
        await page.setInputFiles("input[type=file][multiple]", ["Interview_04_Lea.m4a", "Interview_05_Tom.wav", "Gruppengespraech_Quartier.mp4"]
          .map((name) => ({ name, mimeType: "application/octet-stream", buffer: Buffer.from("demo") })));
        await warte(500);
        try {
          const wahl = page.locator(".rt-SelectTrigger").filter({ hasText: /wählen|Choose|Choisir|Scegli|nombre|numero|speaker count/i });
          for (const [i, wert] of [[0, "2"], [0, "4"]]) {   // nach der ersten Wahl rückt die nächste auf Index 0
            await wahl.nth(i).click();
            await page.locator(".rt-SelectItem").filter({ hasText: new RegExp(`^${wert}$`) }).first().click();
            await warte(200);
          }
        } catch (e) { console.log("  (Sprecherzahl nicht gesetzt:", String(e).split("\n")[0], ")"); }
        await laufHalten();
        await warte(900);                               // die Oberfläche holt den Stand im Takt
        await bild("02-ai-transkript.png");

        await ctx.close();
        console.log(`${sprache} ${modus} ${b * dpr}×${h * dpr} ✓ (Satz)`);
        continue;
      }

      // 01 Editor: Transkript, Sprecher-Panel, Wellenform
      await oeffne({ ...editor, "lt.editor.seitentab": "sprecher" });
      await page.waitForSelector("[data-seg='7']");
      await warte(1200);                               // Wellenform + Höhenmessung
      if (SITE) {
        // Das Hero-Bild trägt die Aussage «du korrigierst» — also muss eine
        // Zeile offen in Bearbeitung sein, nicht bloss ausgewählt.
        const zeile = page.locator("[data-seg='7'] textarea.seg-text");
        await zeile.click();
        await zeile.evaluate((el) => {
          const ende = el.value.indexOf(" ", 46);
          el.setSelectionRange(14, ende > 0 ? ende : el.value.length);
        });
        await warte(300);
      }
      await bild("01-editor.png");
      if (SITE) {
        // Memo-Dialog derselben Zeile — die Website hatte dafür bisher kein Bild
        await page.locator("[data-seg='7'] .lucide-notepad-text").first().click();
        await page.waitForSelector("[role='dialog'] textarea");
        await warte(400);
        await knips("09-memo.png");
        await page.keyboard.press("Escape");
        await warte(200);
      }
      if (HILFE) {
        // 09 Wellenform + Steuerzeile, 11 drei Zeilen (Zeile 7 trägt ein Memo)
        const welle = await page.locator("canvas").last().boundingBox();
        if (welle) await bild("09-wiedergabe.png", { x: welle.x, y: welle.y - 6, width: welle.width, height: h - welle.y + 6 });
        const z0 = await page.locator("[data-seg='6']").boundingBox();
        const z1 = await page.locator("[data-seg='8']").boundingBox();
        if (z0 && z1) await bild("11-zeile.png", { x: z0.x, y: z0.y - 4, width: z0.width, height: z1.y + z1.height - z0.y + 8 });
        // 08 Memo-Dialog der Zeile 7
        await page.locator("[data-seg='7'] .lucide-notepad-text").first().click();
        await page.waitForSelector("[role='dialog'] textarea");
        await warte(400);
        await knips("08-memo.png");
        await page.keyboard.press("Escape");
        await warte(200);
      }

      // 02 AI-Transkript: fertiger Lauf + Warteliste mit Sprecherzahl je Datei
      await oeffne({ "lt.ui.tab": "ai" });
      await page.setInputFiles("input[type=file][multiple]", ["Interview_04_Lea.m4a", "Interview_05_Tom.wav", "Gruppengespraech_Quartier.mp4"]
        .map((name) => ({ name, mimeType: "application/octet-stream", buffer: Buffer.from("demo") })));
      await warte(500);
      // zwei der drei Dateien bekommen ihre Sprecherzahl — die dritte zeigt
      // den Hinweis «Sprecherzahl wählen»
      try {
        const wahl = page.locator(".rt-SelectTrigger").filter({ hasText: /wählen|Choose|Choisir|Scegli|nombre|numero|speaker count/i });
        for (const [i, wert] of [[0, "2"], [0, "4"]]) {     // nach der ersten Wahl rückt die nächste auf Index 0
          await wahl.nth(i).click();
          await page.locator(".rt-SelectItem").filter({ hasText: new RegExp(`^${wert}$`) }).first().click();
          await warte(200);
        }
      } catch (e) { console.log("  (Sprecherzahl nicht gesetzt:", String(e).split("\n")[0], ")"); }
      if (SITE) { await laufHalten(); await warte(900); }   // ein Lauf arbeitet, siehe altBatch
      await bild("02-ai-transkript.png");

      // 03 Bibliothek (Human-Editor)
      await oeffne({ "lt.ui.tab": "editor", "lt.ui.editor": "" });
      await warte(300);
      await bild("03-bibliothek.png");

      // 04 Suchen und Ersetzen
      await oeffne({ ...editor, "lt.editor.seitentab": "suchen" });
      await page.waitForSelector("[data-seg='7']");
      const felder = page.locator(".ui-sidepanel input[type=text], .ui-sidepanel input:not([type])");
      if (await felder.count() >= 2) {
        await felder.nth(0).fill("cooperative");
        await felder.nth(1).fill("co-operative");
      } else {
        await page.locator("input").nth(0).fill("cooperative");
      }
      await warte(900);
      await bild("04-suchen-ersetzen.png");

      // 05 Sprecherfarbe wählen
      await oeffne({ ...editor, "lt.editor.seitentab": "sprecher" });
      await page.waitForSelector("[data-farbwahl] button");
      await warte(900);
      await page.locator("[data-farbwahl] button").first().click();
      await warte(300);
      await knips("05-sprecherfarbe.png");
      await page.keyboard.press("Escape");

      // 06 Export-Formate
      await page.mouse.click(10, h - 10);
      await page.locator(".rt-SelectTrigger.rt-variant-soft").first().click();
      await warte(400);
      await knips("06-export.png");
      await page.keyboard.press("Escape");

      if (SITE) {
        // Video: Editor mit mitlaufendem Bild
        await oeffne({ "lt.ui.tab": "editor", "lt.ui.editor": videoEid, [`lt.editor.aktiv.${videoEid}`]: "3", "lt.editor.seitentab": "sprecher" });
        await page.waitForSelector("[data-seg='3']");
        await warte(1800);
        await bild("video.png");
        // Zotero: Suche mit Treffern, dann verknüpft
        await oeffne({ ...editor, "lt.editor.seitentab": "metadaten" });
        await page.waitForSelector("[data-seg='7']");
        const feld = page.locator(".ui-sidepanel input").first();
        await feld.fill("housing");
        await feld.press("Enter");
        await warte(900);
        await bild("zotero.png");
        try {
          await page.getByText("whitfield2026", { exact: false }).first().click();     // Treffer wählen
          await warte(500);
          await page.locator(".ui-sidepanel button").filter({ hasText: /^(Verknüpfen|Link|Lier|Collega)$/ }).first().click({ timeout: 8000 });
          await warte(900);
        } catch (e) { console.log("  (Zotero nicht verknüpft:", String(e).split("\n")[0], ")"); }
        await bild("zotero-linked.png");
        await api(`/api/transcripts/${eid}/zotero`, { method: "DELETE" }).catch(() => undefined);
      }

      // 07 Einstellungen
      await oeffne({ "lt.ui.tab": "einstellungen" });
      await warte(500);
      await neutralisiere(page);
      await bild("07-einstellungen.png");

      await ctx.close();
      console.log(`${sprache} ${modus} ${b * dpr}×${h * dpr} ✓`);
    }
  }
}
await browser.close();
if (satzLauf) await api(`/api/jobs/${satzLauf}/cancel`, { method: "POST" }).catch(() => undefined);
await api("/api/settings", json({ ui_language: "de" }));
ende();
fs.rmSync(SCRATCH, { recursive: true, force: true });
console.log(`${zahl} Bilder unter ${AUS}`);
process.exit(0);
