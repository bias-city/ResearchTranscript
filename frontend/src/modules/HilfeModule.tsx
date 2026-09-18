// Handbuch (User 2026-09-18): durchsuchbar, viersprachig, mit Bildern in
// Hell und Dunkel. Läuft in einem eigenen Fenster (index.html#hilfe) —
// ohne Backend; die Sprache kommt aus demselben Speicher wie die App.
import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from "react";
import { Flex, Heading, SearchField, Text } from "../components/ui";
import { setSprache, useSprache, useT, type Sprache } from "../lib/i18n";
import { KEYS, lget } from "../lib/storage";
import type { Block, Kapitel } from "../lib/hilfe/typ";

const LADER: Record<Sprache, () => Promise<{ default: Kapitel[] }>> = {
  de: () => import("../lib/hilfe/de"),
  en: () => import("../lib/hilfe/en"),
  fr: () => import("../lib/hilfe/fr"),
  it: () => import("../lib/hilfe/it"),
};

/** Suchform: klein, ohne Akzente, ohne Auszeichnung. */
const norm = (s: string) => s.toLowerCase().normalize("NFD")
  .replace(/[̀-ͯ]/g, "").replace(/\*\*|\[\[|\]\]|`/g, "");

function useDunkel(): boolean {
  const mq = useMemo(() => window.matchMedia("(prefers-color-scheme: dark)"), []);
  const [d, setD] = useState(mq.matches);
  useEffect(() => {
    const h = (e: MediaQueryListEvent) => setD(e.matches);
    mq.addEventListener("change", h);
    return () => mq.removeEventListener("change", h);
  }, [mq]);
  return d;
}

/** Text mit **Beschriftung**, [[Taste]] und Treffer-Markierung. */
function Inline({ text, terme }: { text: string; terme: string[] }) {
  const teile = text.split(/(\*\*[^*]+\*\*|\[\[[^\]]+\]\]|`[^`]+`)/g).filter(Boolean);
  return <>{teile.map((t, i) => {
    if (t.startsWith("**")) return <strong key={i}><Marke text={t.slice(2, -2)} terme={terme} /></strong>;
    if (t.startsWith("`")) return <code key={i} className="hilfe-code"><Marke text={t.slice(1, -1)} terme={terme} /></code>;
    if (t.startsWith("[[")) return <kbd key={i} className="hilfe-kbd">{t.slice(2, -2)}</kbd>;
    return <Marke key={i} text={t} terme={terme} />;
  })}</>;
}

/** Treffer hervorheben — Vergleich in der Suchform, Ausgabe im Original
    (NFD verlängert nur Zeichen mit Akzent; die Abbildung läuft je Zeichen). */
function Marke({ text, terme }: { text: string; terme: string[] }) {
  if (!terme.length) return <>{text}</>;
  const zeichen = [...text];
  const flach = zeichen.map((z) => norm(z) || " ");
  const lang = flach.join("");
  const start: number[] = [];                 // Position in `lang` → Index in `zeichen`
  flach.forEach((f, i) => { for (let k = 0; k < f.length; k++) start.push(i); });
  const an = new Array<boolean>(zeichen.length).fill(false);
  for (const t of terme) {
    for (let p = lang.indexOf(t); p >= 0; p = lang.indexOf(t, p + 1)) {
      for (let k = p; k < p + t.length; k++) an[start[k]] = true;
    }
  }
  const aus: ReactNode[] = [];
  for (let i = 0; i < zeichen.length;) {
    let j = i;
    while (j < zeichen.length && an[j] === an[i]) j++;
    const stueck = zeichen.slice(i, j).join("");
    aus.push(an[i] ? <mark key={i} className="hilfe-mark">{stueck}</mark> : <Fragment key={i}>{stueck}</Fragment>);
    i = j;
  }
  return <>{aus}</>;
}

const passt = (text: string, terme: string[]) => { const n = norm(text); return terme.every((t) => n.includes(t)); };

/** Block auf die Treffer eingrenzen (Listen und Tabellen zeilenweise);
    null = kein Treffer. Bilder zählen über ihre Bildunterschrift. */
function eingrenzen(b: Block, terme: string[]): Block | null {
  switch (b.art) {
    case "p": case "h": case "hinweis": case "bild":
      return passt(b.text, terme) ? b : null;
    case "liste": case "schritte": {
      const punkte = b.punkte.filter((p) => passt(p, terme));
      return punkte.length ? { ...b, art: "liste", punkte } : null;
    }
    case "tasten": {
      const zeilen = b.zeilen.filter((z) => passt(z.join(" "), terme));
      return zeilen.length ? { ...b, zeilen } : null;
    }
    case "tabelle": {
      const zeilen = b.zeilen.filter((z) => passt(z.join(" "), terme));
      return zeilen.length ? { ...b, zeilen } : null;
    }
  }
}

function BlockAnsicht({ b, terme, bildBasis }: { b: Block; terme: string[]; bildBasis: string }) {
  switch (b.art) {
    case "h": return <Heading size="3" mt="4" mb="1"><Inline text={b.text} terme={terme} /></Heading>;
    case "p": return <p className="hilfe-p"><Inline text={b.text} terme={terme} /></p>;
    case "hinweis": return <div className="hilfe-hinweis"><Inline text={b.text} terme={terme} /></div>;
    case "liste": return <ul className="hilfe-liste">{b.punkte.map((p, i) => <li key={i}><Inline text={p} terme={terme} /></li>)}</ul>;
    case "schritte": return <ol className="hilfe-liste">{b.punkte.map((p, i) => <li key={i}><Inline text={p} terme={terme} /></li>)}</ol>;
    case "tasten": return (
      <table className="hilfe-tabelle hilfe-tasten"><tbody>{b.zeilen.map(([t, w], i) => (
        <tr key={i}><td><Inline text={t} terme={terme} /></td><td><Inline text={w} terme={terme} /></td></tr>))}</tbody></table>);
    case "tabelle": return (
      <div style={{ overflowX: "auto" }}><table className="hilfe-tabelle">
        <thead><tr>{b.kopf.map((k, i) => <th key={i}>{k}</th>)}</tr></thead>
        <tbody>{b.zeilen.map((z, i) => <tr key={i}>{z.map((c, k) => <td key={k}><Inline text={c} terme={terme} /></td>)}</tr>)}</tbody>
      </table></div>);
    case "bild": return (
      <figure className="hilfe-bild">
        <img src={`${bildBasis}/${b.datei}.jpg`} alt={b.text} loading="lazy" />
        <figcaption><Inline text={b.text} terme={terme} /></figcaption>
      </figure>);
  }
}

export default function HilfeModule() {
  const tr = useT();
  const sprache = useSprache();
  const dunkel = useDunkel();
  const [kapitel, setKapitel] = useState<Kapitel[]>([]);
  const [offen, setOffen] = useState<string>(() => lget(KEYS.hilfeKapitel) ?? "");
  const [frage, setFrage] = useState("");
  const inhalt = useRef<HTMLDivElement>(null);

  // Sprache folgt der App: anderes Fenster, gleicher Speicher
  useEffect(() => {
    const lies = () => {
      const s = lget(KEYS.sprache);
      if (s && s !== sprache && ["de", "en", "fr", "it"].includes(s)) setSprache(s as Sprache);
    };
    window.addEventListener("storage", lies);
    window.addEventListener("focus", lies);
    return () => { window.removeEventListener("storage", lies); window.removeEventListener("focus", lies); };
  }, [sprache]);

  useEffect(() => {
    let weg = false;
    void LADER[sprache]().then((m) => { if (!weg) setKapitel(m.default); });
    return () => { weg = true; };
  }, [sprache]);
  useEffect(() => { document.title = tr("hilfe.titel"); }, [tr, sprache]);

  const terme = useMemo(() => norm(frage).split(/\s+/).filter((t) => t.length > 1), [frage]);
  const treffer = useMemo(() => {
    if (!terme.length) return null;
    return kapitel.map((k) => {
      const imTitel = passt(`${k.titel} ${k.kurz}`, terme);
      const bloecke = k.bloecke.map((b) => eingrenzen(b, terme)).filter((b): b is Block => b !== null && b.art !== "bild");
      return { k, imTitel, bloecke };
    }).filter((t) => t.imTitel || t.bloecke.length);
  }, [kapitel, terme]);

  const aktiv = kapitel.find((k) => k.id === offen) ?? kapitel[0];
  const bildBasis = `hilfe/${sprache}/${dunkel ? "dunkel" : "hell"}`;
  const oeffne = (id: string) => {
    setOffen(id); setFrage("");
    try { localStorage.setItem(KEYS.hilfeKapitel, id); } catch { /* privat */ }
    inhalt.current?.scrollTo({ top: 0 });
  };
  const zahl = treffer?.reduce((n, t) => n + Math.max(1, t.bloecke.length), 0) ?? 0;

  return (
    <Flex style={{ height: "100vh", background: "var(--color-background)" }}>
      <Flex direction="column" gap="2" p="3" className="hilfe-nav">
        <Heading size="3">{tr("hilfe.titel")}</Heading>
        <SearchField value={frage} onChange={setFrage} placeholder={tr("hilfe.suchen")} />
        {treffer && <Text size="1" color="gray">
          {zahl ? tr("hilfe.treffer", { n: zahl }) : tr("hilfe.keine")}</Text>}
        <nav style={{ overflowY: "auto", flex: 1, margin: "4px -6px 0" }}>
          {kapitel.map((k, i) => {
            const t = treffer?.find((x) => x.k.id === k.id);
            const matt = treffer !== null && !t;
            return (
              <button key={k.id} type="button" disabled={matt}
                      className={`hilfe-navpunkt${!treffer && aktiv?.id === k.id ? " aktiv" : ""}`}
                      onClick={() => {
                        if (!treffer) { oeffne(k.id); return; }
                        document.getElementById(`hilfe-t-${k.id}`)?.scrollIntoView({ block: "start" });
                      }}>
                <span className="hilfe-nr">{i + 1}</span>
                <span style={{ flex: 1 }}>{k.titel}</span>
                {t && <span className="hilfe-zahl">{Math.max(1, t.bloecke.length)}</span>}
              </button>);
          })}
        </nav>
      </Flex>
      <div ref={inhalt} className="hilfe-inhalt">
        <div className="hilfe-spalte">
          {treffer ? (
            treffer.length === 0
              ? <Text color="gray">{tr("hilfe.keine")}</Text>
              : treffer.map(({ k, bloecke }) => (
                <section key={k.id} id={`hilfe-t-${k.id}`} className="hilfe-treffer">
                  <Flex align="baseline" justify="between" gap="3">
                    <Heading size="4"><Marke text={k.titel} terme={terme} /></Heading>
                    <button type="button" className="hilfe-link" onClick={() => oeffne(k.id)}>
                      {tr("hilfe.kapitel")}</button>
                  </Flex>
                  {bloecke.length === 0 && <p className="hilfe-p"><Marke text={k.kurz} terme={terme} /></p>}
                  {bloecke.map((b, i) => <BlockAnsicht key={i} b={b} terme={terme} bildBasis={bildBasis} />)}
                </section>))
          ) : aktiv ? (
            <article>
              <Heading size="6" mb="1">{aktiv.titel}</Heading>
              <Text as="p" size="3" color="gray" mb="3">{aktiv.kurz}</Text>
              {aktiv.bloecke.map((b, i) => <BlockAnsicht key={i} b={b} terme={[]} bildBasis={bildBasis} />)}
              <Flex justify="between" mt="6" gap="3">
                {(() => {
                  const i = kapitel.indexOf(aktiv);
                  const vor = kapitel[i - 1], nach = kapitel[i + 1];
                  return <>
                    {vor ? <button type="button" className="hilfe-link" onClick={() => oeffne(vor.id)}>← {vor.titel}</button> : <span />}
                    {nach ? <button type="button" className="hilfe-link" onClick={() => oeffne(nach.id)}>{nach.titel} →</button> : <span />}
                  </>;
                })()}
              </Flex>
            </article>
          ) : null}
        </div>
      </div>
    </Flex>
  );
}
