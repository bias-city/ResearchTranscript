#!/usr/bin/env node
// Bundle-Resources für den Tauri-Build zusammenstellen:
// python-runtime + whisper-cli/dylibs + Modelle werden aus dem
// alten LocalTranscript-v1-Checkout ÜBERNOMMEN, wenn er daneben liegt
// (whisper-web/electron/resources — dort hat build-python-runtime.mjs
// sie einst gebaut); sonst bricht das Skript mit Anleitung ab.
// Die Python-Pakete werden IMMER FRISCH nach python/site-packages
// installiert (v2-Backend + enrich-core), ohne venv.
//
// Aufruf: node scripts/bundle-resources.mjs
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const RES = path.join(ROOT, "frontend/src-tauri/resources");
const ALT = path.resolve(ROOT, "../whisper-web/electron/resources");
// enrich-core: das öffentliche MIT-Paket, genau der Stand, gegen den
// getestet wird (backend/pyproject.toml [tool.uv.sources]) — nie mehr
// der Geschwister-Checkout, der auch die Analyse-Module trägt.
const ENRICH_CORE = "enrich-core @ git+https://github.com/bias-city/enrich-core@v0.1.0";

function da(p) { try { return fs.statSync(p).isDirectory(); } catch { return false; } }
function leer(p) { try { return fs.readdirSync(p).length === 0; } catch { return true; } }
function kopiere(von, nach) {
  console.log(`kopiere ${von} → ${nach}`);
  fs.rmSync(nach, { recursive: true, force: true });
  fs.cpSync(von, nach, { recursive: true, verbatimSymlinks: true });
}

// 1. Runtime + Binaries + Modelle
for (const teil of ["python-runtime", "bin", "lib", "models"]) {
  const ziel = path.join(RES, teil);
  if (da(ziel) && !leer(ziel)) { console.log(`✓ ${teil} vorhanden`); continue; }
  const quelle = path.join(ALT, teil);
  if (!da(quelle)) {
    console.error(`FEHLT: ${teil} — weder in ${ziel} noch in ${quelle}.`);
    console.error("Erstausstattung: im whisper-web-Checkout `cd electron && npm run build:bundle` laufen lassen (lädt CPython, kopiert whisper-cli/ffmpeg/Modell) — oder die Teile hier von Hand ablegen.");
    process.exit(1);
  }
  kopiere(quelle, ziel);
}

// 1a0. Laufzeit stutzen (Plan §2 Streichliste): Tcl/Tk, tkinter, IDLE,
//      Test-Suite, ensurepip haben in der App nichts zu suchen — sie
//      kosten 30 MB, und die Tcl-Bibliotheken tragen nackte Install-
//      Namen, die der otool-Wächter (R7) zu Recht anmeckert. pip bleibt
//      in der Laufzeit, weil dieses Skript damit installiert.
{
  const rt = path.join(RES, "python-runtime");
  const weg = [
    ...fs.readdirSync(path.join(rt, "lib")).filter((n) =>
      /^(itcl|tcl|tk|thread|libtcl|libtk|libitcl)/.test(n)).map((n) => path.join(rt, "lib", n)),
    ...["tkinter", "idlelib", "ensurepip", "turtledemo", "test", "turtle.py"]
      .map((n) => path.join(rt, "lib/python3.13", n)),
    ...fs.readdirSync(path.join(rt, "lib/python3.13/lib-dynload"))
      .filter((n) => /^_tkinter/.test(n)).map((n) => path.join(rt, "lib/python3.13/lib-dynload", n)),
    path.join(rt, "share"), path.join(rt, "include"),
  ];
  let n = 0;
  for (const p of weg) { if (fs.existsSync(p)) { fs.rmSync(p, { recursive: true, force: true }); n++; } }
  if (n) console.log(`✓ Laufzeit gestutzt: ${n} Einträge (Tcl/Tk, tkinter, IDLE, Tests, ensurepip)`);
}

// 1a. SpeakerKit-Modelle (Core ML) für den Shim im Prozess; die CLI
//     argmax-cli kommt seit 0.6.0 NICHT mehr ins Bundle (nur noch
//     LT_MOTOR=kind im Checkout braucht sie, aus <repo>/bin).
{
  const mdl = path.join(ROOT, "models/speakerkit");
  if (!da(path.join(mdl, "speaker_segmenter"))) {
    console.error("FEHLT: models/speakerkit — einmal `node scripts/hole-argmax.mjs` laufen lassen.");
    process.exit(1);
  }
  kopiere(mdl, path.join(RES, "models/speakerkit"));
  for (const alt of ["bin/argmax-cli", "bin/ffmpeg"]) {
    const p = path.join(RES, alt);
    if (fs.existsSync(p)) { fs.rmSync(p); console.log(`✓ ${alt} entfernt (Motoren im Prozess)`); }
  }
  console.log("✓ SpeakerKit-Modelle im Bundle");
}

// 1a0b. whisper-cli als Tauri-Sidecar (Contents/MacOS, Store: Entitlement
//       inherit). Die ggml-/whisper-Bibliotheken wandern als Frameworks
//       nach Contents/Frameworks; der rpath des Sidecars zeigt dorthin.
{
  const quelle = path.join(RES, "bin/whisper-cli");
  const binDir = path.join(ROOT, "frontend/src-tauri/binaries");
  const ziel = path.join(binDir, "whisper-cli-aarch64-apple-darwin");
  fs.mkdirSync(binDir, { recursive: true });
  fs.copyFileSync(quelle, ziel);
  fs.chmodSync(ziel, 0o755);
  const rpaths = execFileSync("/usr/bin/otool", ["-l", ziel], { encoding: "utf8" });
  if (!rpaths.includes("@loader_path/../Frameworks")) {
    execFileSync("/usr/bin/install_name_tool", ["-add_rpath", "@loader_path/../Frameworks", ziel]);
  }
  console.log("✓ whisper-cli als Sidecar (binaries/, rpath ../Frameworks)");
}

// 1a1. libmp3lame (LGPL, dynamisch) aus eigenem Bau — scripts/baue-lame.sh
{
  const lame = path.join(RES, "frameworks/libmp3lame.dylib");
  if (!fs.existsSync(lame)) {
    console.error("FEHLT: resources/frameworks/libmp3lame.dylib — `scripts/baue-lame.sh` laufen lassen.");
    process.exit(1);
  }
  console.log("✓ libmp3lame.dylib vorhanden");
}

// 1a2. Altlast wegräumen: die SpeechBrain-Gewichte (85 MB) trug das
//      Bundle bis 2.4.3 für die alte Sprechertrennung — seit 2.5.0
//      rührt sie kein Code mehr an.
{
  const alt = path.join(RES, "models/speechbrain");
  if (da(alt)) { fs.rmSync(alt, { recursive: true, force: true });
                 console.log("✓ alte SpeechBrain-Modelle entfernt (85 MB)"); }
}

// 2. Python-Pakete DIREKT nach python/site-packages (Plan §4 1.13):
//    kein venv mehr. Das venv war ein Symlink-Gebilde mit pyvenv.cfg,
//    die auf einen absoluten Pfad zeigte — im Worktree installierte pip
//    prompt in den falschen Checkout (Befund 17.9.2026), und Tauri
//    dereferenzierte die Symlinks beim Bündeln. Jetzt: die gebündelte
//    Laufzeit installiert mit --target in einen flachen Ordner, den
//    python.rs als einzigen site-packages-Pfad setzt (site_import=0).
//    Nur die Prozess-Abhängigkeiten (pydantic, enrich-core) — kein
//    fastapi/uvicorn: der Server ist ein Extra für Browser-Dev.
const SITE = path.join(RES, "python/site-packages");
const py = path.join(RES, "python-runtime/bin/python3");
{
  fs.rmSync(path.join(RES, "venv"), { recursive: true, force: true });
  fs.rmSync(SITE, { recursive: true, force: true });
  fs.mkdirSync(SITE, { recursive: true });
  console.log("installiere researchtranscript + enrich-core …");
  execFileSync(py, ["-m", "pip", "install", "--quiet", "--no-compile",
                    "--target", SITE, ENRICH_CORE, path.join(ROOT, "backend")],
               { stdio: "inherit" });
  // pip legt unter --target ein bin/ mit Startskripten an — weg damit
  fs.rmSync(path.join(SITE, "bin"), { recursive: true, force: true });
  // Wächter: site_import=0 verarbeitet keine .pth-Dateien — eine
  // Abhängigkeit, die darauf baut, würde im Bundle still fehlen.
  const pth = fs.readdirSync(SITE).filter((n) => n.endsWith(".pth"));
  if (pth.length) {
    console.error(`ABBRUCH: .pth-Dateien in site-packages (${pth.join(", ")}) — python.rs lädt keine.`);
    process.exit(1);
  }
  // Wächter: nichts vom Server im Bundle, nichts mit fremdem Pfad
  for (const verboten of ["fastapi", "uvicorn", "starlette"]) {
    if (fs.existsSync(path.join(SITE, verboten))) {
      console.error(`ABBRUCH: ${verboten} im Bundle — pyproject-Abhängigkeiten prüfen.`);
      process.exit(1);
    }
  }
  // Der Import-Smoke-Test läuft in sign-resources.mjs NACH dem Signieren:
  // python3 der Laufzeit trägt Team-ID + Hardened Runtime, ein frisch
  // installiertes pydantic_core.so noch nicht — vorher verweigert die
  // Library-Validation das Laden («different Team IDs»).
  console.log("✓ python/site-packages installiert");
}

// 3. Marker
fs.writeFileSync(path.join(RES, "BUNDLED"),
                 `ResearchTranscript bundle ${new Date().toISOString()}\n`);
console.log("Resources bereit:", RES);
