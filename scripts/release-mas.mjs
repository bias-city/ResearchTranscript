#!/usr/bin/env node
// Mac-App-Store-Build (Plan §6): Ressourcen → Signatur der Teile → App mit
// «Apple Distribution» und Store-Entitlements → .pkg mit «Mac Installer
// Distribution» → Prüfungen → Upload (altool mit API-Schlüssel).
//
// Voraussetzungen (einmalig, Apple-Portal): App-ID city.bias.researchtranscript
// mit App Sandbox; Zertifikate «Apple Distribution» und «Mac Installer
// Distribution» im Schlüsselbund; Profil unter
// frontend/src-tauri/profiles/ResearchTranscript.provisionprofile;
// API-Schlüssel ~/.appstoreconnect/private_keys/AuthKey_<ID>.p8 mit
// APPLE_API_KEY_ID und APPLE_API_ISSUER in der Umgebung.
//
// Aufruf: node scripts/release-mas.mjs [--upload] [--identity <Distribution-Hash>]
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const TAURI = path.join(ROOT, "frontend/src-tauri");
const APP = path.join(TAURI, "target/release/bundle/macos/ResearchTranscript.app");
const PKG = path.join(TAURI, "target/release/bundle/macos/ResearchTranscript.pkg");
const PROFIL = path.join(TAURI, "profiles/ResearchTranscript.provisionprofile");
const upload = process.argv.includes("--upload");
const sh = (cmd, args, opts = {}) => execFileSync(cmd, args, { stdio: "inherit", cwd: ROOT, ...opts });
const out = (cmd, args) => execFileSync(cmd, args, { encoding: "utf8", cwd: ROOT });

function identitaet(name) {
  const liste = out("/usr/bin/security", ["find-identity", "-v", "-p", "codesigning"]);
  const m = liste.split("\n").find((z) => z.includes(name));
  if (!m) { console.error(`ABBRUCH: Zertifikat «${name}» fehlt im Schlüsselbund — im Apple-Portal erzeugen und importieren.`); process.exit(1); }
  return m.trim().split(" ")[1];
}
const DIST = process.argv.includes("--identity") ? process.argv[process.argv.indexOf("--identity") + 1]
  : identitaet("Apple Distribution:");
const INSTALLER = (() => {
  // Das Portal nennt es «Mac Installer Distribution», im Schlüsselbund heisst
  // es «3rd Party Mac Developer Installer: …». Keine codesigning-Identität —
  // deshalb über find-identity OHNE -p codesigning suchen.
  const alle = out("/usr/bin/security", ["find-identity", "-v"]);
  const z = alle.split("\n").find((l) => l.includes("3rd Party Mac Developer Installer") || l.includes("Mac Installer Distribution"));
  if (!z) { console.error("ABBRUCH: Installer-Zertifikat fehlt («Mac Installer Distribution» im Portal, im Schlüsselbund «3rd Party Mac Developer Installer»)."); process.exit(1); }
  return z.match(/"([^"]+)"/)[1];
})();
if (!fs.existsSync(PROFIL)) { console.error(`ABBRUCH: Provisioning-Profil fehlt: ${PROFIL}`); process.exit(1); }

console.log("1/6 Ressourcen");
sh("node", [path.join(ROOT, "scripts/bundle-resources.mjs")]);
console.log("2/6 Teile signieren (Apple Distribution)");
sh("node", [path.join(ROOT, "scripts/sign-resources.mjs"), "--identity", DIST]);
console.log("3/6 App bauen (Store-Konfiguration, ohne Devtools)");
sh("npx", ["tauri", "build", "--bundles", "app", "--config", "tauri.macos-appstore.conf.json", "--", "--no-default-features", "--features", "motoren"],
   { cwd: path.join(ROOT, "frontend"), env: { ...process.env, PYO3_CONFIG_FILE: path.join(TAURI, "pyo3-config.txt"),
     APPLE_ID: undefined, APPLE_PASSWORD: undefined, APPLE_TEAM_ID: undefined } });
sh("node", [path.join(ROOT, "scripts/nachsignieren.mjs"), APP, "--mas", "--identity", DIST]);
console.log("4/6 Prüfungen");
sh("/usr/bin/codesign", ["--verify", "--deep", "--strict", "--verbose=2", APP]);
const ent = out("/usr/bin/codesign", ["-d", "--entitlements", "-", "--xml", APP]);
for (const k of ["com.apple.security.app-sandbox", "com.apple.application-identifier", "com.apple.security.network.client"]) {
  if (!ent.includes(k)) { console.error(`ABBRUCH: Entitlement ${k} fehlt in der Hülle`); process.exit(1); }
}
if (!fs.existsSync(path.join(APP, "Contents/embedded.provisionprofile"))) { console.error("ABBRUCH: embedded.provisionprofile fehlt im Bundle"); process.exit(1); }
const kind = out("/usr/bin/codesign", ["-d", "--entitlements", "-", "--xml", path.join(APP, "Contents/MacOS/whisper-cli")]);
if (!kind.includes("com.apple.security.inherit")) { console.error("ABBRUCH: whisper-cli ohne inherit-Entitlement"); process.exit(1); }
const otool = out("/usr/bin/otool", ["-L", path.join(APP, "Contents/MacOS/ResearchTranscript")]);
if (/\t\/(opt|usr\/local|Users)\//.test(otool)) { console.error("ABBRUCH: Hülle hängt an einem absoluten Fremdpfad:\n" + otool); process.exit(1); }
console.log("5/6 Installer-Paket");
fs.rmSync(PKG, { force: true });
sh("/usr/bin/xcrun", ["productbuild", "--sign", INSTALLER, "--component", APP, "/Applications", PKG]);
sh("/usr/sbin/pkgutil", ["--check-signature", PKG]);
console.log(`Paket: ${PKG} (${(fs.statSync(PKG).size / 1e6).toFixed(0)} MB)`);
if (upload) {
  const { APPLE_API_KEY_ID, APPLE_API_ISSUER } = process.env;
  if (!APPLE_API_KEY_ID || !APPLE_API_ISSUER) { console.error("ABBRUCH: APPLE_API_KEY_ID / APPLE_API_ISSUER fehlen"); process.exit(1); }
  console.log("6/6 Validieren und hochladen (App Store Connect)");
  sh("/usr/bin/xcrun", ["altool", "--validate-app", "--type", "macos", "--file", PKG, "--apiKey", APPLE_API_KEY_ID, "--apiIssuer", APPLE_API_ISSUER]);
  sh("/usr/bin/xcrun", ["altool", "--upload-app", "--type", "macos", "--file", PKG, "--apiKey", APPLE_API_KEY_ID, "--apiIssuer", APPLE_API_ISSUER]);
} else {
  console.log("6/6 übersprungen — mit --upload validieren und hochladen (Transporter.app geht auch).");
}
