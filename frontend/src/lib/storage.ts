// Sichere Storage-Zugriffe (enrich-Kit-Muster): Private Mode / Quota
// werfen — das UI darf daran nie sterben. Schlüssel zentral.
export const KEYS = {
  sprache: "lt.ui.sprache",
  optionenOffen: "lt.bibliothek.optionen",
  editorFolgen: "lt.editor.folgen",
  editorSpeed: "lt.editor.speed",
  sidebarSprecher: "lt.editor.sprecher-panel",
  editorSeitenTab: "lt.editor.seitentab",
  // Die App startet dort, wo sie beendet wurde (User 2026-09-17): Tab,
  // offenes Transkript, aktives Segment je Transkript (Präfix + ID)
  tab: "lt.ui.tab",
  editorOffen: "lt.ui.editor",
  editorAktiv: "lt.editor.aktiv.",
} as const;

export function sget(key: string): string | null {
  try { return sessionStorage.getItem(key); } catch { return null; }
}
export function sset(key: string, value: string): void {
  try { sessionStorage.setItem(key, value); } catch { /* Quota */ }
}
export function lget(key: string): string | null {
  try { return localStorage.getItem(key); } catch { return null; }
}
export function lset(key: string, value: string): void {
  try { localStorage.setItem(key, value); } catch { /* Private Mode */ }
}
