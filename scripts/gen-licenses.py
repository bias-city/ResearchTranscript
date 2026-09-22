#!/usr/bin/env python3
"""Drittanbieter-Lizenzen von allem, was in der App steckt (Plan §6).

Sammelt
  - Rust-Crates der Hülle (cargo metadata + cargo tree, nur normale
    Abhängigkeiten für das Ziel, keine Bauwerkzeuge),
  - npm-Pakete des Frontends (Laufzeit-Abhängigkeiten aus package.json
    samt transitiven aus node_modules),
  - Python-Pakete aus resources/python/site-packages (dist-info),
  - die festen Bestandteile ausserhalb der Paketverwalter: whisper.cpp,
    ggml, Modelle, SpeakerKit, CPython, LAME,
und schreibt THIRD_PARTY_LICENSES.md (Tabelle + vollständige Texte).
Die Datei kommt ins Bundle (Resources/licenses) und ist über den Knopf
«Lizenzen» in den Einstellungen erreichbar. Muster: PrepareMedia
scripts/gen-licenses.py.

Aufruf: python3 scripts/gen-licenses.py [--target aarch64-apple-darwin]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TAURI = ROOT / "frontend/src-tauri"
FRONTEND = ROOT / "frontend"
SITE_PACKAGES = TAURI / "resources/python/site-packages"
AUS = ROOT / "THIRD_PARTY_LICENSES.md"
LICENSE_FILE = re.compile(r"^(licen[cs]e|copying|notice|unlicense|copyright)([-._].*)?$", re.I)

APP_VERSION = json.loads((FRONTEND / "package.json").read_text())["version"]

#: Lizenztexte der festen Bestandteile. Sie liegen als Dateien im Repo
#: (lizenztexte/), weil sie nicht aus einem Paketverwalter kommen: teils aus
#: dem Quellarchiv (LAME), teils aus der gebündelten Laufzeit (CPython), teils
#: aus dem Projekt-Repository (whisper.cpp, Whisper, Silero, SpeakerKit,
#: swift-argument-parser) und einmal der Lizenzvolltext selbst (CC BY 4.0).
#: App Review 22.9.2026: vorher trug die Tabelle für genau diese Bestandteile
#: keinen einzigen Lizenztext, obwohl README und App das zusagen.
TEXTE_DIR = ROOT / "lizenztexte"

#: Bestandteile ohne Paketverwalter — Version, Lizenz, Quelle, Hinweis, Textdatei
FESTE = [
    ("whisper.cpp (whisper-cli, libwhisper, ggml)", "1.8.2", "MIT",
     "https://github.com/ggml-org/whisper.cpp",
     "Als Hilfsprogramm `whisper-cli` und Bibliotheken im Bundle (Metal).", "whisper.cpp.txt"),
    ("Whisper large-v3-turbo (ggml)", "large-v3-turbo", "MIT (OpenAI)",
     "https://github.com/openai/whisper · https://huggingface.co/ggerganov/whisper.cpp",
     "Sprachmodell, im Bundle unter Resources/models.", "whisper-openai.txt"),
    ("Silero VAD (ggml)", "v5.1.2", "MIT",
     "https://github.com/snakers4/silero-vad", "Sprachaktivitätserkennung für whisper.cpp.", "silero-vad.txt"),
    ("SpeakerKit (argmax-oss-swift)", "ea872ff", "MIT (Teile Apache-2.0, siehe NOTICES)",
     "https://github.com/argmaxinc/argmax-oss-swift",
     "Sprechertrennung, statisch in die App gelinkt (Swift-Paket RTMotoren). Der Text enthält die NOTICES des Projekts.", "speakerkit.txt"),
    # Ausgeliefert wird Argmax' Core-ML-Fassung; deren Modellkarte nennt
    # CC BY 4.0 («The models SpeakerKit is built on have CC BY 4 license»).
    # Eine Kopie der Karte liegt unter models/speakerkit/README.hf.md.
    ("SpeakerKit-Modelle (Core ML): Segmentierung, Sprecher-Embeddings, Clustering",
     "Core ML (Argmax)", "CC BY 4.0", "https://huggingface.co/argmaxinc/speakerkit-coreml",
     "Von Argmax umgewandelt und quantisiert; Ursprungsmodelle pyannote segmentation-3.0 "
     "und WeSpeaker ResNet34 / pyannote community-1. Namensnennung nach CC BY 4.0: Argmax Inc. "
     "sowie die Urheber der Ursprungsmodelle.", "cc-by-4.0.txt"),
    ("CPython (python-build-standalone)", "3.13", "PSF-2.0 (Python Software Foundation License)",
     "https://github.com/astral-sh/python-build-standalone",
     "Eingebetteter Interpreter (libpython3.13.dylib), führt nur die mitgelieferten Skripte aus.", "cpython.txt"),
    ("LAME", "4.0", "LGPL-2.0-or-later",
     "https://lame.sourceforge.io · Quelle wie mitgeliefert: https://bias.city/researchtranscript/quellen/lame-4.0.tar.gz",
     "MP3-Kodierung; dynamisch gelinkt (Contents/Frameworks/libmp3lame.dylib), ohne Decoder gebaut "
     "(scripts/baue-lame.sh), damit die Bibliothek ausgetauscht werden kann.", "lame.txt"),
    ("swift-argument-parser", "1.8.2", "Apache-2.0",
     "https://github.com/apple/swift-argument-parser", "Abhängigkeit von argmax-oss-swift.", "swift-argument-parser.txt"),
]


def cargo(*args: str) -> str:
    env = dict(os.environ)
    env["PATH"] = os.path.expanduser("~/.cargo/bin") + os.pathsep + env.get("PATH", "")
    env.setdefault("PYO3_CONFIG_FILE", str(TAURI / "pyo3-config.txt"))
    return subprocess.run(["cargo", *args], cwd=TAURI, env=env, check=True,
                          capture_output=True, text=True).stdout


def lizenzdateien(ordner: Path) -> list[Path]:
    try:
        return sorted(p for p in ordner.iterdir()
                      if p.is_file() and LICENSE_FILE.match(p.name) and p.stat().st_size < 300_000)
    except OSError:
        return []


def lies(p: Path) -> str:
    return p.read_text(encoding="utf-8", errors="replace").strip()


def crates(target: str) -> list[dict]:
    meta = json.loads(cargo("metadata", "--format-version", "1"))
    tree = cargo("tree", "-e", "normal", "--target", target, "--prefix", "none", "-f", "{p}")
    gewollt = set()
    for zeile in tree.splitlines():
        m = re.match(r"^(\S+) v(\S+)", zeile.strip())
        if m:
            gewollt.add((m.group(1), m.group(2)))
    wurzel = next(p for p in meta["packages"] if Path(p["manifest_path"]).parent == TAURI)
    aus = []
    for p in sorted(meta["packages"], key=lambda p: (p["name"].lower(), p["version"])):
        if (p["name"], p["version"]) not in gewollt or p["id"] == wurzel["id"]:
            continue
        ordner = Path(p["manifest_path"]).parent
        aus.append({"art": "Rust", "name": p["name"], "version": p["version"],
                    "lizenz": p.get("license") or "siehe Lizenzdatei",
                    "quelle": p.get("repository") or p.get("homepage") or f"https://crates.io/crates/{p['name']}",
                    "texte": [lies(f) for f in lizenzdateien(ordner)]})
    return aus


def npm_pakete() -> list[dict]:
    """Laufzeit-Abhängigkeiten laut `npm ls --omit=dev` (transitiv)."""
    try:
        baum = json.loads(subprocess.run(["npm", "ls", "--omit=dev", "--all", "--json"],
                                         cwd=FRONTEND, capture_output=True, text=True).stdout)
    except (ValueError, OSError):
        return []
    gesehen: dict[tuple[str, str], dict] = {}

    def geh(deps: dict) -> None:
        for name, d in (deps or {}).items():
            v = d.get("version", "")
            # ohne Version = nicht installiert/nur Peer/extraneous — nicht im Bundle
            if not v or d.get("extraneous") or d.get("missing") or (name, v) in gesehen:
                continue
            ordner = FRONTEND / "node_modules" / name
            try:
                pj = json.loads((ordner / "package.json").read_text())
            except (OSError, ValueError):
                pj = {}
            liz = pj.get("license") or (pj.get("licenses") or [{}])[0].get("type") or "siehe Lizenzdatei"
            repo = pj.get("repository")
            if isinstance(repo, dict):
                repo = repo.get("url", "")
            gesehen[(name, v)] = {"art": "npm", "name": name, "version": v, "lizenz": liz,
                                  "quelle": (repo or pj.get("homepage") or f"https://www.npmjs.com/package/{name}")
                                  .replace("git+", "").replace("git://", "https://").removesuffix(".git"),
                                  "texte": [lies(f) for f in lizenzdateien(ordner)]}
            geh(d.get("dependencies") or {})
    geh(baum.get("dependencies") or {})
    return sorted(gesehen.values(), key=lambda p: p["name"].lower())


def python_pakete() -> list[dict]:
    aus = []
    for info in sorted(SITE_PACKAGES.glob("*.dist-info")):
        meta = {}
        try:
            for zeile in (info / "METADATA").read_text(encoding="utf-8", errors="replace").splitlines():
                if not zeile.strip():
                    break
                if ":" in zeile:
                    k, v = zeile.split(":", 1)
                    meta.setdefault(k.strip(), v.strip())
                    if k.strip() == "Classifier" and "License ::" in v:
                        meta.setdefault("_klassifikation", v.split("::")[-1].strip())
        except OSError:
            continue
        name = meta.get("Name", info.name.split("-")[0])
        if name.lower() == "researchtranscript":
            continue
        liz = meta.get("License-Expression") or meta.get("_klassifikation") or meta.get("License") or "siehe Lizenzdatei"
        if len(liz) > 60:
            liz = meta.get("_klassifikation") or "siehe Lizenzdatei"
        quelle = meta.get("Home-page") or ""
        for zeile in (info / "METADATA").read_text(encoding="utf-8", errors="replace").splitlines():
            if zeile.startswith("Project-URL:") and ("Source" in zeile or "Repository" in zeile or "Homepage" in zeile):
                quelle = zeile.split(",", 1)[-1].strip()
                break
        texte = [lies(f) for f in lizenzdateien(info)] + [lies(f) for f in lizenzdateien(info / "licenses")]
        aus.append({"art": "Python", "name": name, "version": meta.get("Version", "?"), "lizenz": liz,
                    "quelle": quelle or f"https://pypi.org/project/{name}/", "texte": texte})
    return aus


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="aarch64-apple-darwin")
    a = ap.parse_args()
    pakete = crates(a.target) + npm_pakete() + python_pakete()
    texte: dict[str, dict] = {}
    for p in pakete:
        p["ids"] = []
        for t in p["texte"]:
            h = hashlib.sha1(t.encode()).hexdigest()[:10]
            e = texte.setdefault(h, {"id": h, "text": t, "pakete": []})
            e["pakete"].append(f"{p['name']} {p['version']}")
            p["ids"].append(h)

    z = [f"# Drittanbieter-Lizenzen · ResearchTranscript {APP_VERSION}", "",
         f"ResearchTranscript ist freie Software unter der GNU AGPL, Version 3 oder später (LICENSE), "
         f"mit einer Zusatzerlaubnis für den App Store (LICENSE-EXCEPTION). Die App enthält die folgenden "
         f"Bestandteile (Stand dieses Builds, Ziel {a.target}). Die WebView (WebKit) stellt macOS; sie ist nicht Teil der App.",
         "", "## Bestandteile ausserhalb der Paketverwalter", "",
         "| Bestandteil | Version | Lizenz | Quelle | Hinweis | Text |", "|---|---|---|---|---|---|"]
    for name, ver, liz, quelle, hinweis, textdatei in FESTE:
        datei = TEXTE_DIR / textdatei
        if not datei.is_file():
            raise SystemExit(f"ABBRUCH: Lizenztext fehlt: {datei}")
        t = datei.read_text(encoding="utf-8").strip()
        h = hashlib.sha1(t.encode()).hexdigest()[:10]
        e = texte.setdefault(h, {"id": h, "text": t, "pakete": []})
        e["pakete"].append(f"{name} {ver}")
        z.append(f"| {name} | {ver} | {liz} | {quelle} | {hinweis} | [{h}](#text-{h}) |")
    for art, titel in (("Rust", "Rust-Crates der Hülle"), ("npm", "npm-Pakete der Oberfläche"),
                       ("Python", "Python-Pakete")):
        teil = [p for p in pakete if p["art"] == art]
        z += ["", f"## {titel} ({len(teil)})", "", "| Paket | Version | Lizenz | Quelle | Text |", "|---|---|---|---|---|"]
        for p in teil:
            refs = ", ".join(f"[{h}](#text-{h})" for h in p["ids"]) or "—"
            z.append(f"| {p['name']} | {p['version']} | {p['lizenz']} | {p['quelle']} | {refs} |")
    z += ["", "## Lizenztexte", "",
          "Jeder Text einmal; die Kennung verweist aus den Tabellen hierher.", ""]
    for e in sorted(texte.values(), key=lambda e: (-len(e["pakete"]), e["id"])):
        z += [f"### Text {e['id']} <a id=\"text-{e['id']}\"></a>", "",
              "Gilt für: " + ", ".join(e["pakete"]), "", "```", e["text"], "```", ""]
    AUS.write_text("\n".join(z) + "\n", encoding="utf-8")
    print(f"{AUS.name}: {len(FESTE)} feste Bestandteile (alle mit Lizenztext), "
          f"{len(pakete)} Pakete, {len(texte)} Lizenztexte")


if __name__ == "__main__":
    main()
