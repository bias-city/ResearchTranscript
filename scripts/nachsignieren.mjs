#!/usr/bin/env node
// NACH `tauri build`: Tauri signiert den Sidecar whisper-cli mit den
// Entitlements der Hülle — in der Sandbox braucht ein Kind aber genau
// `app-sandbox` + `inherit` (Phase-0-Messung 5), sonst bekommt es einen
// eigenen Container und sieht das WAV der Hülle nicht. Also: Sidecar mit
// entitlements.child.plist neu signieren und die Hülle neu versiegeln.
//
// Aufruf: node scripts/nachsignieren.mjs [pfad.app] [--mas] [--identity <hash>]
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TAURI = path.join(ROOT, "frontend/src-tauri");
const args = process.argv.slice(2);
const app = args.find((a) => a.endsWith(".app")) ?? path.join(TAURI, "target/release/bundle/macos/ResearchTranscript.app");
const mas = args.includes("--mas");
const idArg = args.indexOf("--identity");
const conf = JSON.parse(fs.readFileSync(path.join(TAURI, "tauri.conf.json"), "utf8"));
const id = idArg >= 0 ? args[idArg + 1] : conf.bundle.macOS.signingIdentity;
const huelle = path.join(TAURI, mas ? "entitlements.mas.plist" : "entitlements.plist");
const kind = path.join(TAURI, "entitlements.child.plist");
const sidecar = path.join(app, "Contents/MacOS/whisper-cli");
if (!fs.existsSync(sidecar)) { console.error(`Sidecar fehlt: ${sidecar}`); process.exit(1); }
const sign = (ent, ziel) => execFileSync("/usr/bin/codesign",
  ["--force", "--sign", id, "--options", "runtime", "--timestamp", "--entitlements", ent, ziel], { stdio: "inherit" });
// Die Python-Programme (python, python3, pip …) braucht nur der Bau: die App
// bettet libpython ein und startet nie einen Interpreter als Kind. Im Bundle
// wären sie ausführbare Programme OHNE Sandbox-Entitlement — App Store
// Connect lehnt das ab (Fehler 90296, 18.9.2026), und mit dem Entitlement
// signiert stürzen sie ab (SIGTRAP, Phase 3). Also heraus damit, in beiden
// Kanälen; resources/python-runtime/bin bleibt für den nächsten Bau erhalten.
const pybin = path.join(app, "Contents/Resources/python-runtime/bin");
if (fs.existsSync(pybin)) { fs.rmSync(pybin, { recursive: true }); console.log("entfernt: python-runtime/bin (nur Bauwerkzeug)"); }
sign(kind, sidecar);
sign(huelle, app);
execFileSync("/usr/bin/codesign", ["--verify", "--deep", "--strict", app], { stdio: "inherit" });
const ent = execFileSync("/usr/bin/codesign", ["-d", "--entitlements", "-", "--xml", sidecar], { encoding: "utf8", stdio: ["ignore", "pipe", "ignore"] });
if (!ent.includes("com.apple.security.inherit")) { console.error("ABBRUCH: inherit fehlt auf whisper-cli"); process.exit(1); }
console.log(`nachsigniert: whisper-cli (inherit), Hülle (${path.basename(huelle)})`);
