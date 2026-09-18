#!/usr/bin/env node
// App-Icons aus frontend/src-tauri/icons/logo.svg (User 2026-09-18).
//
// macOS-Raster: 1024er Leinwand, das Zeichen 824 px hoch mittig (100 px
// Rand ringsum — so sitzen Mac-Icons im Dock gleich gross wie die
// anderen), Ecken transparent. Gerendert mit Playwright-WebKit
// (omitBackground), verkleinert mit sips, gebündelt mit iconutil.
// Ergebnis: icons/icon.icns (16–1024 inkl. @2x), 128x128.png, 32x32.png,
// dazu site/img/logo.svg und app-icon-1024.png für den App Store.
import { execFileSync } from "node:child_process";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { createRequire } from "node:module";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const require = createRequire(path.join(ROOT, "frontend/package.json"));
const { webkit } = require("playwright");
const ICONS = path.join(ROOT, "frontend/src-tauri/icons");
const svg = fs.readFileSync(path.join(ICONS, "logo.svg"), "utf8");
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), "rt-icons-"));

const browser = await webkit.launch();
const page = await browser.newPage({ viewport: { width: 1024, height: 1024 }, deviceScaleFactor: 1 });
const uri = "data:image/svg+xml;base64," + Buffer.from(svg).toString("base64");
await page.setContent(`<html><body style="margin:0;background:transparent">
  <div style="width:1024px;height:1024px;display:flex;align-items:center;justify-content:center">
    <img src="${uri}" style="height:824px;width:auto;display:block"></div></body></html>`);
await page.waitForFunction(() => document.images[0]?.complete);
const gross = path.join(tmp, "1024.png");
await page.screenshot({ path: gross, omitBackground: true });
await browser.close();

const iconset = path.join(tmp, "icon.iconset");
fs.mkdirSync(iconset);
for (const [name, px] of [["16x16", 16], ["16x16@2x", 32], ["32x32", 32], ["32x32@2x", 64], ["128x128", 128],
  ["128x128@2x", 256], ["256x256", 256], ["256x256@2x", 512], ["512x512", 512], ["512x512@2x", 1024]]) {
  execFileSync("/usr/bin/sips", ["-z", String(px), String(px), gross, "--out", path.join(iconset, `icon_${name}.png`)], { stdio: "ignore" });
}
execFileSync("/usr/bin/iconutil", ["-c", "icns", iconset, "-o", path.join(ICONS, "icon.icns")]);
fs.copyFileSync(path.join(iconset, "icon_128x128.png"), path.join(ICONS, "128x128.png"));
fs.copyFileSync(path.join(iconset, "icon_32x32.png"), path.join(ICONS, "32x32.png"));
fs.mkdirSync(path.join(ROOT, "appstore"), { recursive: true });
fs.copyFileSync(gross, path.join(ROOT, "appstore/app-icon-1024.png"));
fs.copyFileSync(path.join(ICONS, "logo.svg"), path.join(ROOT, "site/img/logo.svg"));
fs.rmSync(tmp, { recursive: true, force: true });
console.log("Icons gebaut:", fs.readdirSync(ICONS).join(", "));
