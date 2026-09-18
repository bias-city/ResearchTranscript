#!/usr/bin/env node
// Schreibt frontend/src-tauri/pyo3-config.txt für DIESEN Rechner.
// PyO3 verlangt absolute Pfade auf die gebündelte Python-Laufzeit; die Datei
// ist deshalb erzeugt und nicht eingecheckt (.gitignore), damit kein
// Rechnerpfad ins Repo oder in ein Quellarchiv wandert.
// Läuft am Ende von bundle-resources.mjs; einzeln: node scripts/pyo3-config.mjs
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TAURI = path.join(ROOT, "frontend/src-tauri");
const RT = path.join(TAURI, "resources/python-runtime");

export function schreibePyo3Config() {
  const ziel = path.join(TAURI, "pyo3-config.txt");
  fs.writeFileSync(ziel, [
    "implementation=CPython",
    "version=3.13",
    "shared=true",
    "abi3=false",
    "lib_name=python3.13",
    `lib_dir=${path.join(RT, "lib")}`,
    `executable=${path.join(RT, "bin/python3")}`,
    "pointer_width=64",
    "build_flags=",
    "suppress_build_script_link_lines=false",
    "",
  ].join("\n"));
  return ziel;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  console.log("✓", schreibePyo3Config());
}
