// Wächter für App-Store-Richtlinie 2.5.2 («Apps should be self-contained … may not
// download, install, or execute code»).
//
// Hintergrund: Apple hat 0.6.0 am 22.9.2026 abgelehnt, weil ein Textscan
// «itms-services» im Paket fand — eine Datenkonstante aus CPythons `urllib/parse.py`.
// Im selben Paket lagen ausserdem pip mit PyPI-Adresse und Installationsbefehlen,
// `venv`, der CPython-Bauordner und ein Shell-Skript, das per `svn export` Code von
// einem fremden Server holt. Nichts davon braucht die App.
//
// Diese Prüfung läuft an zwei Stellen: in `bundle-resources.mjs` auf dem
// zusammengestellten Ressourcenbaum und in `release-mas.mjs` noch einmal auf dem
// fertigen Bundle — denn nur Letzteres wird eingereicht.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";

/** Ordner, die im Auslieferungspaket nichts zu suchen haben, mit Grund. */
const VERBOTENE_ORDNER = {
  pip: "Paketverwalter (lädt und installiert Code)",
  ensurepip: "richtet pip ein",
  setuptools: "Paketbau",
  distutils: "Paketbau",
  venv: "legt Python-Umgebungen an",
  "config-3.13-darwin": "CPython-Bauordner (Makefile, install-sh, makesetup)",
  pkgconfig: "Bau-Metadaten",
};

/** Dateien, die als Installations- oder Ladewerkzeug gelesen werden. */
const VERBOTENE_DATEIEN = [
  { muster: /\.exe$/i, grund: "ausführbare Windows-Datei" },
  { muster: /^fetch_macholib(\.bat)?$/, grund: "holt Quellcode per svn von einem fremden Server" },
  { muster: /^pip-.*\.dist-info$/, grund: "Metadaten des Paketverwalters" },
];

/** Zeichenketten, die ein Scan als Installationsweg liest. */
const VERBOTENE_TEXTE = ["itms-services"];

function suche(wurzel, unterordner, ausnahmen) {
  const pfade = unterordner.map((u) => path.join(wurzel, u)).filter((p) => fs.existsSync(p));
  if (!pfade.length) throw new Error(`Prüfung 2.5.2: keiner dieser Pfade existiert: ${unterordner.join(", ")}`);
  const ausser = ausnahmen.map((a) => path.join(wurzel, a));
  const raus = (p) => ausser.some((a) => p === a || p.startsWith(a + "/"));
  const funde = [];

  // Namen: ein Durchlauf über den Baum, dann in JS filtern.
  let liste = "";
  try {
    liste = execFileSync("/usr/bin/find", [...pfade, "-maxdepth", "12"], { encoding: "utf8", maxBuffer: 64 << 20 });
  } catch (e) {
    liste = e.stdout || "";
  }
  for (const zeile of liste.split("\n")) {
    if (!zeile) continue;
    if (raus(zeile)) continue;
    const name = path.basename(zeile);
    if (VERBOTENE_ORDNER[name]) funde.push(`${zeile} — ${VERBOTENE_ORDNER[name]}`);
    for (const { muster, grund } of VERBOTENE_DATEIEN) {
      if (muster.test(name)) funde.push(`${zeile} — ${grund}`);
    }
  }

  // Texte: grep meldet mit Code 1, dass nichts gefunden wurde.
  for (const text of VERBOTENE_TEXTE) {
    let treffer = "";
    try {
      treffer = execFileSync("/usr/bin/grep", ["-rl", text, ...pfade], { encoding: "utf8", maxBuffer: 64 << 20 });
    } catch { /* nichts gefunden */ }
    for (const zeile of treffer.split("\n").filter(Boolean)) {
      if (!raus(zeile)) funde.push(`${zeile} — enthält «${text}»`);
    }
  }
  return funde;
}

/**
 * Prüft `wurzel`/`unterordner` und bricht den Lauf ab, wenn etwas gefunden wird.
 * `ausnahmen` sind Pfade relativ zu `wurzel`, die nicht ins Auslieferungspaket
 * gelangen — im Ressourcenbaum ist das `python-runtime/bin` (die Startprogramme
 * von Python und pip, die der Bau braucht; `nachsignieren.mjs` entfernt sie in
 * BEIDEN Kanälen aus dem fertigen Bundle, und die zweite Prüfung im
 * release-mas.mjs sieht genau dorthin).
 * Gibt bei Erfolg eine Meldung für die Ausgabe zurück.
 */
export function pruefe2_5_2(wurzel, unterordner, ausnahmen = []) {
  const funde = suche(wurzel, unterordner, ausnahmen);
  if (funde.length) {
    console.error("ABBRUCH: Guideline 2.5.2 — das Paket enthält Werkzeuge oder Zeichenketten,");
    console.error("die Apple als «lädt oder installiert Code» liest:\n");
    for (const f of funde.slice(0, 40)) console.error("  " + f);
    if (funde.length > 40) console.error(`  … und ${funde.length - 40} weitere`);
    console.error("\nSiehe scripts/pruefung-2-5-2.mjs und die Streichliste in bundle-resources.mjs.");
    process.exit(1);
  }
  return `✓ Prüfung 2.5.2: kein pip, kein venv, kein Bauordner, keine .exe, kein itms-services (${unterordner.join(", ")})`;
}
