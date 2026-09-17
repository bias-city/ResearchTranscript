// Tauri-Brücke: Feature-Detection + die wenigen nativen Wege (Save-/
// Open-Dialoge, Ordner öffnen, Protokoll, Neustart). Python läuft im
// Prozess der Hülle — es gibt nichts mehr zu starten.
export function isTauri(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/** Pfad des Protokolls der Hülle (Python-Ausgaben, Fehler, Herzschlag). */
export async function protokollPfad(): Promise<string | null> {
  if (!isTauri()) return null;
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<string | null>("protokoll_pfad");
}

/** Hülle neu starten (nach «Verarbeitung blockiert»). */
export async function neustart(): Promise<void> {
  if (!isTauri()) { window.location.reload(); return; }
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("neustart");
}

/** Herzschlag der Hülle: true, wenn Python 10 s nicht antwortet,
    false, sobald es wieder antwortet. */
export async function onBlockiert(cb: (blockiert: boolean) => void):
    Promise<() => void> {
  if (!isTauri()) return () => {};
  const { listen } = await import("@tauri-apps/api/event");
  return listen<boolean>("blockiert", (e) => cb(e.payload));
}

export async function savePath(defaultName: string,
                               ext: string): Promise<string | null> {
  const { save } = await import("@tauri-apps/plugin-dialog");
  return save({
    defaultPath: defaultName,
    filters: [{ name: ext.toUpperCase(), extensions: [ext] }],
  });
}

export async function pickAudio(title?: string,
                                multiple = true):
    Promise<string[] | null> {
  const { open } = await import("@tauri-apps/plugin-dialog");
  const r = await open({ multiple, title, filters: [{
    name: "Audio / Video",
    extensions: ["mp3", "m4a", "aac", "wav", "ogg", "flac",
                 "mp4", "m4v", "mov"] }] });
  if (r == null) return null;
  return Array.isArray(r) ? r : [r];
}

export async function pickTranskript(): Promise<string | null> {
  const { open } = await import("@tauri-apps/plugin-dialog");
  const r = await open({ multiple: false, filters: [{
    name: "Transkript",
    extensions: ["vtt", "webvtt", "csv", "enrich", "zip"] }] });
  return typeof r === "string" ? r : null;
}

export async function pickOrdner(): Promise<string | null> {
  const { open } = await import("@tauri-apps/plugin-dialog");
  const r = await open({ directory: true, multiple: false });
  return typeof r === "string" ? r : null;
}

export async function ordnerOeffnen(pfad: string): Promise<void> {
  if (!isTauri()) return;
  const { invoke } = await import("@tauri-apps/api/core");
  await invoke("ordner_oeffnen", { pfad });
}

/** Nativer Datei-Drop (Tauri fängt HTML5-DnD ab und liefert PFADE —
    genau richtig: große Audios laufen nie durch HTTP). */
export async function onFileDrop(
  cb: (paths: string[]) => void): Promise<() => void> {
  if (!isTauri()) return () => {};
  const { getCurrentWebview } = await import("@tauri-apps/api/webview");
  return getCurrentWebview().onDragDropEvent((e) => {
    if (e.payload.type === "drop") cb(e.payload.paths);
  });
}

/** Dateien, die macOS der App zum Öffnen gab (Doppelklick auf ein
    .enrich im Finder, «Öffnen mit»). Die Shell sammelt sie; dieser
    Aufruf holt und leert die Liste — auch das, was vor dem ersten
    Listener ankam (Start per Doppelklick). */
export async function geoeffneteDateien(): Promise<string[]> {
  if (!isTauri()) return [];
  const { invoke } = await import("@tauri-apps/api/core");
  return invoke<string[]>("geoeffnete_dateien");
}

/** Signal der Shell, dass neue Dateien zum Öffnen da sind — die Pfade
    holt der Aufrufer über geoeffneteDateien(), damit nichts doppelt
    importiert wird. */
export async function onDateien(cb: () => void): Promise<() => void> {
  if (!isTauri()) return () => {};
  const { listen } = await import("@tauri-apps/api/event");
  return listen("dateien", () => cb());
}

/** „About ResearchTranscript" aus dem Menü — die Shell schickt nur das
    Signal, den Dialog baut das Frontend (übersetzt, mit Links). */
export async function onUeber(cb: () => void): Promise<() => void> {
  if (!isTauri()) return () => {};
  const { listen } = await import("@tauri-apps/api/event");
  return listen("ueber", () => cb());
}
