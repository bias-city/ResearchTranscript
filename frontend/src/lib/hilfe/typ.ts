// Handbuch-Inhalt (User 2026-09-18): je Sprache EINE Datei (de/en/fr/it)
// mit denselben Kapitel-ids und Bilddateien; de ist die Quellsprache.
// Inline-Auszeichnung im Text: **Beschriftung der Oberfläche**,
// [[Taste]] für Tasten. Bilder liegen unter
// public/hilfe/<sprache>/<hell|dunkel>/<datei>.jpg und entstehen mit
// `node scripts/appstore-screenshots.mjs --hilfe`.
export type Block =
  | { art: "p"; text: string }
  | { art: "h"; text: string }
  | { art: "hinweis"; text: string }
  | { art: "liste"; punkte: string[] }
  | { art: "schritte"; punkte: string[] }
  | { art: "tasten"; zeilen: [tasten: string, wirkung: string][] }
  | { art: "tabelle"; kopf: string[]; zeilen: string[][] }
  | { art: "bild"; datei: string; text: string };

export type Kapitel = { id: string; titel: string; kurz: string; bloecke: Block[] };
