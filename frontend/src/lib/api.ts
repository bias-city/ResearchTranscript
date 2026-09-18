// API-Typen + Transport — EINE Stelle (enrich-Kit-Regel).
//
// Zwei Transporte hinter denselben Signaturen (Plan §4 1.11):
// - Tauri: `invoke("api", {name, args})` an die Python-Fassade IM
//   Prozess (kein HTTP, kein Port). Die Pfade unten werden auf die
//   Befehlsnamen von backend/src/researchtranscript/api.py abgebildet —
//   dieselbe Tabelle wie main.py, nur rückwärts.
// - Browser (Vite-Dev, Playwright, Screenshots): `fetch` gegen den
//   Vite-Proxy → uvicorn auf 5628.
import { beginne, ende } from "./busy";
import { isTauri } from "./tauri";

/** Dev-Server-Adresse (nur Browser-Betrieb; der Vite-Proxy leitet /api
    weiter). Port 5628 = „LOCT" auf der Telefontastatur, enrich-Muster;
    lebt an EINER Stelle je Sprache (config.py · vite.config.ts · hier). */
export const BACKEND_PORT = 5628;
export const API_BASE = "";

export type Sprecher = { id: string; name: string;
  /** gewählte Farbe (Radix-Name aus FARB_AUSWAHL); ohne: nach Reihenfolge */
  farbe?: string | null };
export type Segment = {
  id: string; start: number; end: number;
  sprecher: string | null; text: string;
  /** Memo der forschenden Person zu dieser Zeile — kein Teil des
      Wortlauts; geht in CSV und REFI-QDA mit */
  memo?: string | null;
};
export type Transkript = {
  schema: number; id: string; name: string; created: string;
  updated: string; audio: string | null;
  /** Video unverändert im Eintrag (BACKLOG 8); der Ton liegt als mp3 daneben */
  video?: string | null;
  quelle: Record<string, unknown>;
  sprecher: Sprecher[]; segmente: Segment[];
  /** Zotero-Schnappschuss, wenn verknüpft */
  zotero?: ZoteroMeta | null;
};
export type EintragMeta = {
  id: string; name: string; created: string; updated: string;
  dauer: number; segmente: number; sprecher: number; audio: boolean;
  video?: boolean;
  quelle: Record<string, unknown>;
};
export type Job = {
  id: string; filename: string; status: string; progress: number;
  message: string; partial_text: string; error: string | null;
  eintrag: string | null; created_at: string;
  /** gesetzt, sobald der Job wirklich rechnet (nicht mehr wartet) */
  started_at: string | null;
  params: Record<string, unknown>;
};
export type Settings = {
  library_root: string; default_library_root: string; model: string;
  language: string; diarize: boolean; speaker_range: string;
  /** gleichzeitige Läufe, 1–4 (Standard 1 = nacheinander) */
  max_parallel: number;
  cluster_threshold: number; ui_language: string;
  /** freiwillig: steht als Person im Journal exportierter Dossiers */
  user_email: string;
  /** zufällige Kennung dieser Installation (nie Gerät, nie Person) */
  install_id: string;
  /** Zotero: lokale zotero.sqlite lesen — nur mit Einwilligung */
  zotero_consent: boolean;
  /** leer = Standardorte suchen (~/Zotero, Zotero-Profil, Volumes) */
  zotero_dir: string;
};
/** found = null: ohne Einwilligung wird nicht gesucht */
export type ZoteroStatus = { consent: boolean; found: boolean | null;
                             dir: string | null };
export type ZoteroCreator = { first: string; last: string; role: string };
/** ein Treffer der Kandidatensuche (schlank: ohne Abstract) */
export type ZoteroKandidat = {
  item_key: string; title: string | null; year: string | null;
  date: string | null; item_type: string | null; citekey: string | null;
  creators: ZoteroCreator[]; publication: string | null;
  library: string | null; select_link: string | null; score: number;
};
/** der Schnappschuss im Transkript (origin: source) */
export type ZoteroMeta = {
  item_key: string; citekey: string | null; item_type: string | null;
  title: string | null; date: string | null; year: string | null;
  publication: string | null; doi: string | null; abstract: string | null;
  select_link: string | null; creators: ZoteroCreator[];
  rollen?: string[]; origin?: string; imported_at?: string;
};
export type ModellInfo = { name: string; size_mb: number;
                           quelle: "bundled" | "eigen" };
export type ModellListe = {
  models: ModellInfo[]; models_dir: string; eigene_dir: string | null;
  ungueltig: { datei: string; grund: string }[];
};

export function errMsg(e: unknown): string {
  if (e instanceof Error) return e.message;
  // Fehler der Fassade kommen aus Tauri als `{status, detail}`
  if (e && typeof e === "object" && "detail" in e) {
    return String((e as { detail: unknown }).detail);
  }
  return String(e);
}

// ---------- Tauri: Pfad → Befehl ----------

type Befehl = { name: string; args: Record<string, unknown> };

/** Dieselbe Tabelle wie main.py (Route → Fassade), hier rückwärts.
    Unbekannte Pfade sind ein Programmierfehler, keine Laufzeitfrage. */
function befehl(method: string, pfad: string, body: unknown): Befehl {
  const u = new URL(pfad, "http://x");
  const p = u.pathname;
  const q = u.searchParams;
  const m = (re: RegExp) => p.match(re);
  const args = (body ?? {}) as Record<string, unknown>;
  let t: RegExpMatchArray | null;
  if (p === "/api/health") return { name: "health", args: {} };
  if (p === "/api/models") return { name: "models", args: {} };
  if (p === "/api/settings") {
    return method === "GET" ? { name: "settings_get", args: {} }
                            : { name: "settings_post", args: { aend: args } };
  }
  if (p === "/api/transcribe-path") return { name: "transcribe_path", args: { args } };
  if (p === "/api/import-path") return { name: "import_path", args: { args } };
  if (p === "/api/warteliste") {
    return method === "PUT" ? { name: "warteliste_set", args: { eintraege: body ?? [] } }
                            : { name: "warteliste_get", args: {} };
  }
  if (p === "/api/jobs") return { name: "jobs_liste", args: {} };
  if ((t = m(/^\/api\/jobs\/([^/]+)\/cancel$/))) return { name: "job_cancel", args: { job_id: t[1] } };
  if ((t = m(/^\/api\/jobs\/([^/]+)$/))) return { name: "job_get", args: { job_id: t[1] } };
  if (p === "/api/zotero/status") return { name: "zotero_status", args: {} };
  if (p === "/api/zotero/candidates") return { name: "zotero_candidates", args: { q: q.get("q") ?? "" } };
  if (p === "/api/transcripts") return { name: "transcripts", args: {} };
  if ((t = m(/^\/api\/transcripts\/([^/]+)\/zotero$/))) {
    return method === "DELETE" ? { name: "zotero_unlink", args: { eid: t[1] } }
                               : { name: "zotero_link", args: { eid: t[1], args } };
  }
  if ((t = m(/^\/api\/transcripts\/([^/]+)\/wellenform$/))) {
    return { name: "wellenform", args: { eid: t[1], t0: Number(q.get("t0") ?? 0),
             t1: Number(q.get("t1") ?? 0), buckets: Number(q.get("buckets") ?? 1) } };
  }
  if ((t = m(/^\/api\/transcripts\/([^/]+)\/rename$/))) return { name: "transcript_rename", args: { eid: t[1], args } };
  if ((t = m(/^\/api\/transcripts\/([^/]+)\/delete$/))) return { name: "transcript_delete", args: { eid: t[1], args } };
  if ((t = m(/^\/api\/transcripts\/([^/]+)\/export$/))) return { name: "export_datei", args: { eid: t[1], args } };
  if ((t = m(/^\/api\/transcripts\/([^/]+)$/))) {
    return method === "PUT" ? { name: "transcript_put", args: { eid: t[1], args } }
                            : { name: "transcript_get", args: { eid: t[1] } };
  }
  throw new Error(`Kein Befehl für ${method} ${pfad}`);
}

async function invokeApi<T>(method: string, pfad: string,
                            body?: unknown): Promise<T> {
  const { invoke } = await import("@tauri-apps/api/core");
  const b = befehl(method, pfad, body);
  try {
    return await invoke<T>("api", { name: b.name, args: b.args });
  } catch (e) {
    throw new Error(errMsg(e));
  }
}

// ---------- Browser: fetch ----------

async function _check(r: Response): Promise<Response> {
  if (!r.ok) {
    let detail = `${r.status}`;
    try {
      const j = await r.json();
      if (j && typeof j.detail === "string") detail = j.detail;
    } catch { /* Klartext reicht */ }
    throw new Error(detail);
  }
  return r;
}

export async function apiGet<T>(pfad: string): Promise<T> {
  beginne();
  try {
    if (isTauri()) return await invokeApi<T>("GET", pfad);
    const r = await _check(await fetch(`${API_BASE}${pfad}`));
    return await (r.json() as Promise<T>);
  } finally { ende(); }
}

export async function apiSend<T>(pfad: string, body?: unknown,
                                 method = "POST"): Promise<T> {
  beginne();
  try {
    if (isTauri()) return await invokeApi<T>(method, pfad, body);
    const r = await _check(await fetch(`${API_BASE}${pfad}`, {
      method,
      headers: body === undefined ? undefined
        : { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    }));
    return await (r.json() as Promise<T>);
  } finally { ende(); }
}

/** Multipart-Upload — NUR Browser: in der App laufen Dateien als Pfade
    (Drop, Dialog), nie durch einen Upload. */
export async function apiUpload<T>(pfad: string,
                                   form: FormData): Promise<T> {
  if (isTauri()) throw new Error("Upload nur im Browser-Betrieb");
  beginne();
  try {
    const r = await _check(await fetch(`${API_BASE}${pfad}`,
                                       { method: "POST", body: form }));
    return await (r.json() as Promise<T>);
  } finally { ende(); }
}

// ---------- Medien ----------

/** Adresse für <audio>/<video>: in der App eine asset://-URL auf die
    Bibliotheksdatei (Range durch Tauri, Phase-0-Befund F2), im Browser
    die Streaming-Route. */
export async function medienUrl(eid: string,
                                art: "audio" | "video"): Promise<string> {
  if (!isTauri()) return `${API_BASE}/api/transcripts/${eid}/${art}`;
  const { convertFileSrc, invoke } = await import("@tauri-apps/api/core");
  const r = await invoke<{ path: string }>("medien_pfad", { eid, art });
  return convertFileSrc(r.path);
}

/** Hörprobe eines Sprechers: in der App kommen die WAV-Bytes über den
    IPC und werden zur Blob-URL (revoke() beim Stopp — kein Leck), im
    Browser die Route. */
export async function sprecherProbe(eid: string, sid: string):
    Promise<{ url: string; revoke: () => void }> {
  if (!isTauri()) {
    return { url: `${API_BASE}/api/transcripts/${eid}/sprecher/${sid}/sample`,
             revoke: () => undefined };
  }
  const { invoke } = await import("@tauri-apps/api/core");
  let bytes: ArrayBuffer;
  try {
    bytes = await invoke<ArrayBuffer>("sprecher_probe", { eid, sid });
  } catch (e) { throw new Error(errMsg(e)); }
  const url = URL.createObjectURL(new Blob([bytes], { type: "audio/wav" }));
  return { url, revoke: () => URL.revokeObjectURL(url) };
}

/** Job-Änderungen als Ereignis (App: `job` aus jobs.py, gedrosselt auf
    10 Hz je Job). Im Browser gibt es kein Ereignis — der Aufrufer
    pollt dort weiter. Liefert die Abmeldefunktion. */
export async function onJobs(cb: (job: Job) => void):
    Promise<() => void> {
  if (!isTauri()) return () => undefined;
  const { listen } = await import("@tauri-apps/api/event");
  return listen<Job>("job", (e) => cb(e.payload));
}

/** Farbpalette für Sprecher-Chips (Radix-Badge-Farben, Index = stabil
    über die Entitäts-Reihenfolge). */
export const SPRECHER_FARBEN = [
  "indigo", "amber", "green", "crimson", "teal", "violet", "orange",
  "cyan", "pink", "lime",
] as const;

/** Farben, die sich per Klick auf die Farbmarke wählen lassen (User
    2026-09-17): die Palette plus zehn weitere Radix-Farben. Kein
    System-Farbdialog — Badges, Wellenform und QDPX kennen nur die
    benannten Radix-Skalen, ein freies RGB hätte keine Hell/Dunkel-
    Varianten. Gespeichert in transkript.json als `sprecher[].farbe`. */
export const FARB_AUSWAHL = [
  ...SPRECHER_FARBEN, "tomato", "ruby", "plum", "purple", "blue",
  "sky", "mint", "grass", "brown", "gold",
] as const;
export type Farbe = (typeof FARB_AUSWAHL)[number];

export function sprecherFarbe(sprecher: Sprecher[], sid: string | null):
    Farbe | "gray" {
  if (!sid) return "gray";
  const i = sprecher.findIndex((s) => s.id === sid);
  if (i < 0) return "gray";
  const eigene = sprecher[i].farbe;
  if (eigene && (FARB_AUSWAHL as readonly string[]).includes(eigene)) {
    return eigene as Farbe;
  }
  return SPRECHER_FARBEN[i % SPRECHER_FARBEN.length];
}

/** Lange Namen MITTIG kürzen — die Endung bleibt sichtbar
    (User 2026-08-30: „abc…lmn.mp3"). */
export function kuerze(name: string, max = 56): string {
  if (name.length <= max) return name;
  const kopf = Math.ceil((max - 1) * 0.6);
  const fuss = max - 1 - kopf;
  return `${name.slice(0, kopf)}…${name.slice(-fuss)}`;
}

/** IMMER hh:mm:ss (User-Regel). */
export function hms(sekunden: number): string {
  const s = Math.max(0, Math.floor(sekunden));
  const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60);
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${
    String(s % 60).padStart(2, "0")}`;
}
