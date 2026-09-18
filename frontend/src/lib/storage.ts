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
  // Schriftgrösse des Turn-Texts in px (User 2026-09-17), Standard 13
  editorSchrift: "lt.editor.schrift",
  // Schriftart des Turn-Texts: «sans» (Systemschrift) oder «serif»
  editorFamilie: "lt.editor.familie",
  hilfeKapitel: "lt.hilfe.kapitel",
} as const;

export const TURN_SCHRIFT_STANDARD = 13;
export const TURN_SCHRIFT_WAHL = [12, 13, 14, 15, 16, 18, 20] as const;

/** Schriftgrösse des Turn-Texts anwenden (CSS-Variable) und merken;
    der Editor hört auf «rt-schrift» und misst seine Felder neu. */
export function turnSchriftSetzen(px: number, merken = true): void {
  document.documentElement.style.setProperty("--rt-turn-schrift", `${px}px`);
  if (merken) lset(KEYS.editorSchrift, String(px));
  window.dispatchEvent(new CustomEvent("rt-schrift", { detail: px }));
}
export function turnSchrift(): number {
  const n = Number(lget(KEYS.editorSchrift));
  return (TURN_SCHRIFT_WAHL as readonly number[]).includes(n) ? n : TURN_SCHRIFT_STANDARD;
}

/** Serifenschriften, die macOS mitbringt — die App verweist nur darauf und
    liefert keine Schriftdatei mit (keine Lizenzfrage). `ui-serif` ist auf
    dem Mac «New York»; die übrigen sind Rückfälle. */
export const TURN_SERIF = 'ui-serif, "New York", "Iowan Old Style", Charter, Georgia, serif';
export type TurnFamilie = "sans" | "serif";

/** Schriftart des Turn-Texts anwenden und merken; der Editor misst neu,
    weil Serifenschrift anders läuft (Zeilenumbrüche, Feldhöhen). */
export function turnFamilieSetzen(f: TurnFamilie, merken = true): void {
  const stil = document.documentElement.style;
  if (f === "serif") stil.setProperty("--rt-turn-familie", TURN_SERIF);
  else stil.removeProperty("--rt-turn-familie");
  if (merken) lset(KEYS.editorFamilie, f);
  window.dispatchEvent(new CustomEvent("rt-schrift", { detail: f }));
}
export function turnFamilie(): TurnFamilie {
  return lget(KEYS.editorFamilie) === "serif" ? "serif" : "sans";
}

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
