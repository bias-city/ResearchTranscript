// App-Rahmen: Boot-Gate (Einstellungen laden), First-Run (Speicherort),
// dann Bibliothek ⇄ Editor (Drilldown, enrich-Werkstatt-Muster) +
// Einstellungen. Python läuft im Prozess der Hülle (Variante A) — es
// gibt kein Backend mehr zu starten; der Herzschlag der Hülle meldet,
// wenn die Verarbeitung hängt (Plan R4).
import { useCallback, useEffect, useState } from "react";
import { Badge, Busy, Button, ErrorNote, Flex, Heading, ModalDialog,
  SegTabs, Text } from "./components/ui";
import { Icon } from "./components/icons";
import { apiGet, apiSend, errMsg, type Settings } from "./lib/api";
import { setSprache, useT, type Sprache } from "./lib/i18n";
import { KEYS, lget, lset } from "./lib/storage";
import { geoeffneteDateien, isTauri, lizenzenPfad, neustart, onBlockiert,
  onDateien, onUeber, ordnerMerken, ordnerOeffnen, pickOrdner, standardOrdner,
  vertriebskanal } from "./lib/tauri";
import AiTranscriptModule from "./modules/AiTranscriptModule";
import EditorModule from "./modules/EditorModule";
import EinstellungenModule from "./modules/EinstellungenModule";
import HumanEditorModule from "./modules/HumanEditorModule";

type Boot = "lade" | "bereit" | "fehler";

export default function App() {
  const tr = useT();
  const [boot, setBoot] = useState<Boot>("lade");
  const [bootFehler, setBootFehler] = useState("");
  const [settings, setSettings] = useState<Settings | null>(null);
  // Drei Tabs (User 2026-08-30): AI-Transcript (Default) |
  // Human-Editor (Bibliotheks-Spiegel + Import, Editor-Drilldown) |
  // Einstellungen
  // Wiederaufnahme: Tab und offenes Transkript wie beim Beenden; ein
  // Transkript, das es nicht mehr gibt, fällt beim Laden auf die
  // Bibliothek zurück (EditorModule meldet den Fehler, onExit räumt)
  const [tab, setTab] = useState<"ai" | "editor" | "einstellungen">(() => {
    const g = lget(KEYS.tab);
    return g === "editor" || g === "einstellungen" ? g : "ai";
  });
  const [editorId, setEditorId] = useState<string | null>(
    () => lget(KEYS.editorOffen) || null);
  useEffect(() => { lset(KEYS.tab, tab); }, [tab]);
  useEffect(() => { lset(KEYS.editorOffen, editorId ?? ""); }, [editorId]);
  const [ueber, setUeber] = useState(false);
  const [importFehler, setImportFehler] = useState("");
  const [blockiert, setBlockiert] = useState(false);

  // Dateien aus dem Finder (Doppelklick, «Öffnen mit»): importieren und
  // das zuletzt importierte Transkript im Editor öffnen
  const oeffneDateien = useCallback(async () => {
    const pfade = await geoeffneteDateien();
    let letzte: string | null = null;
    for (const p of pfade) {
      if (!/\.(enrich|enrich\.zip|vtt|webvtt|csv)$/i.test(p)) continue;
      try {
        const r = await apiSend<{ eintrag: string }>("/api/import-path",
                                                     { path: p });
        letzte = r.eintrag;
      } catch (e) { setImportFehler(errMsg(e)); }
    }
    if (letzte) { setTab("editor"); setEditorId(letzte); }
  }, []);

  const starte = useCallback(async () => {
    setBoot("lade");
    try {
      const s = await apiGet<Settings>("/api/settings");
      setSettings(s);
      if (s.ui_language) setSprache(s.ui_language as Sprache);
      setBoot("bereit");
    } catch (e) {
      setBootFehler(errMsg(e));
      setBoot("fehler");
    }
  }, []);
  useEffect(() => { void starte(); }, [starte]);
  useEffect(() => {
    if (boot !== "bereit") return;
    let ab: (() => void) | undefined;
    let weg = false;
    void oeffneDateien();
    void onDateien(() => void oeffneDateien())
      .then((f) => { if (weg) f(); else ab = f; });
    return () => { weg = true; ab?.(); };
  }, [boot, oeffneDateien]);
  // Herzschlag der Hülle: Python antwortet nicht mehr → Banner
  useEffect(() => {
    let ab: (() => void) | undefined;
    let weg = false;
    void onBlockiert(setBlockiert)
      .then((f) => { if (weg) f(); else ab = f; });
    return () => { weg = true; ab?.(); };
  }, []);
  // „About ResearchTranscript" aus dem Menü
  useEffect(() => {
    let ab: (() => void) | undefined;
    let weg = false;
    void onUeber(() => setUeber(true))
      .then((f) => { if (weg) f(); else ab = f; });
    return () => { weg = true; ab?.(); };
  }, []);

  if (boot !== "bereit") {
    return (
      <Flex align="center" justify="center" direction="column" gap="3"
            style={{ height: "100vh" }}>
        <Heading size="5">{tr("app.titel")}</Heading>
        <Text size="2" color="gray">{tr("app.untertitel")}</Text>
        {boot === "lade"
          ? <Text size="2">{tr("app.boot")}</Text>
          : <>
              <Badge color="red">{tr("app.bootfehler")}</Badge>
              <Text size="1" color="gray"
                    style={{ maxWidth: 480, whiteSpace: "pre-wrap" }}>
                {bootFehler}</Text>
              <Button size="1" variant="soft" color="gray" highContrast onClick={() => void starte()}>
                {tr("app.nochmal")}</Button>
            </>}
      </Flex>
    );
  }

  if (settings && !settings.library_root) {
    return <FirstRun onDone={(s) => setSettings(s)} />;
  }

  return (
    <Flex direction="column" style={{ height: "100vh" }}>
      {blockiert && (
        <Flex align="center" gap="3" px="4" py="2"
              style={{ background: "var(--red-a3)",
                       borderBottom: "1px solid var(--red-a6)" }}>
          <Text size="2" style={{ flex: 1 }}>{tr("app.blockiert")}</Text>
          <Button size="1" color="red" variant="soft"
                  onClick={() => void neustart()}>
            {tr("app.neustart")}</Button>
        </Flex>
      )}
      {/* Der Name stand doppelt (native Leiste + App-Kopf). Behoben
          über hiddenTitle: die NATIVE Fensterleiste bleibt — sie ist
          die Greiffläche, an der man das Fenster zieht —, nur ihr
          Titeltext ist aus. Der Name steht damit einmal, hier.

          NICHT über titleBarStyle "Overlay" (Versuch 2026-09-09,
          zurückgenommen): das nimmt die native Leiste ganz weg, die
          Tabs kleben an der Fensterkante, und der Ersatz
          data-tauri-drag-region tut NICHTS, solange die Capability
          core:window:allow-start-dragging fehlt — das Fenster ließ
          sich überhaupt nicht mehr verschieben.

          Der eigene Grauton trennt den Kopf sichtbar vom Inhalt. */}
      <Flex align="center" gap="3" px="4" py="2"
            style={{ borderBottom: "1px solid var(--gray-a5)",
                     background: "var(--gray-a3)" }}>
        {/* Der Name steht in der Menüleiste — hier läuft im Editor der
            Timecode, sonst bleibt der Platz leer (User 2026-09-17) */}
        <KopfZeit schluessel={editorId ?? tab} />
        <Busy />
        <div style={{ flex: 1 }} />
        {/* im Editor-Drilldown ist KEIN Tab aktiv — so feuert der
            Klick auf „Human-Editor" ein onChange und verlässt den
            Editor zur Liste (Review-Befund) */}
        <SegTabs value={editorId ? "" : tab}
                 onChange={(v) => { setEditorId(null); setImportFehler("");
                   setTab(v as "ai" | "editor" | "einstellungen"); }}
                 options={[
                   { value: "ai", label: tr("tab.ai"),
                     icon: "sample" },
                   { value: "editor", label: tr("tab.editor"),
                     icon: "edit" },
                   { value: "einstellungen",
                     label: tr("tab.einstellungen"),
                     icon: "settings" }]} />
      </Flex>
      {importFehler && <ErrorNote>{importFehler}</ErrorNote>}
      <div style={{ flex: 1, minHeight: 0 }}>
        {editorId
          ? <EditorModule id={editorId}
                          onExit={() => setEditorId(null)} />
          : tab === "ai"
            ? <AiTranscriptModule settings={settings}
                onEdit={(id) => { setTab("editor");
                  setEditorId(id); }} />
            : tab === "editor"
              ? <HumanEditorModule
                  onOpen={(id) => setEditorId(id)} />
              : <EinstellungenModule settings={settings}
                                     onChange={setSettings} />}
      </div>
      <UeberDialog open={ueber} onClose={() => setUeber(false)} />
    </Flex>
  );
}

const REPO = "https://github.com/bias-city/ResearchTranscript";
const BIAS = "https://bias.city/researchtranscript/";

/** Eigener Über-Dialog: das macOS-Standardpanel zeigt nur Name und
    Version, und Links darin wären nicht klickbar. Die Texte kommen aus
    denselben Schlüsseln wie die Einstellungs-Karten — EINE Quelle. */
function UeberDialog({ open, onClose }: {
  open: boolean; onClose: () => void;
}) {
  const tr = useT();
  // Die APP-Version steht fest im Build. Die Backend-Version wird nur
  // dazugesetzt, wenn sie abweicht — dann spricht die App mit einem
  // fremden Backend, und das soll man sehen.
  const [backend, setBackend] = useState("");
  useEffect(() => {
    if (!open || backend) return;
    void apiGet<{ version: string }>("/api/health")
      .then((h) => setBackend(h.version)).catch(() => undefined);
  }, [open, backend]);
  const version = backend && backend !== __APP_VERSION__
    ? `${__APP_VERSION__} · Backend ${backend}`
    : __APP_VERSION__;
  // Store-Fassung: kein Verweis auf GitHub-Releases (Aktualisierungen
  // kommen über den App Store), dafür der Hinweis auf die Zusatzerlaubnis
  const [kanal, setKanal] = useState<"mas" | "dmg">("dmg");
  useEffect(() => { void vertriebskanal().then(setKanal); }, []);
  const link = (label: string, url: string) => (
    <Button size="1" variant="soft" color="gray" highContrast onClick={() => void ordnerOeffnen(url)}>
      {label}</Button>
  );
  return (
    <ModalDialog open={open} onOpenChange={(o) => !o && onClose()}
                 title={tr("ueber.titel")} width={520}
                 footer={<Button size="1" variant="soft" color="gray" highContrast onClick={onClose}>
                   {tr("allg.schliessen")}</Button>}>
      <Flex direction="column" gap="3">
        <Flex direction="column" gap="1">
          <Heading size="4">{tr("app.titel")}</Heading>
          <Text size="1" color="gray">
            {tr("ueber.version", { v: version })}</Text>
          <Text size="2" color="gray">{tr("st.app.sub")}</Text>
          <Text size="1" color="gray">{tr("ueber.copyright")}</Text>
        </Flex>
        <Text size="2">{tr("ueber.herkunft")}</Text>
        <Text size="2">{tr("st.app.text")}</Text>
        <Text size="2">{tr(kanal === "mas" ? "ueber.store" : "ueber.erlaubnis")}</Text>
        <Flex gap="2" wrap="wrap">
          {link(tr("st.link.repo"), REPO)}
          {kanal === "dmg" && link(tr("st.link.releases"), `${REPO}/releases`)}
          {link(tr("st.link.lizenztext"), `${REPO}/blob/main/LICENSE`)}
          {link(tr("st.link.erlaubnis"), `${REPO}/blob/main/LICENSE-EXCEPTION`)}
          {link(tr("st.link.datenschutz"), `${BIAS}privacy.html`)}
          {isTauri() && (
            <Button size="1" variant="soft" color="gray" highContrast onClick={() =>
              void lizenzenPfad().then((p) => { if (p) void ordnerOeffnen(p); })}>
              {tr("st.link.lizenzliste")}</Button>
          )}
          {link("BIAS.City", BIAS)}
        </Flex>
        <Text size="1" color="gray">{tr("st.lizenzen.text")}</Text>
        <Text size="1" color="gray">{tr("st.agpl")}</Text>
        <Flex gap="2" wrap="wrap">
          {link(tr("st.link.lamesrc"), "https://lame.sourceforge.io/")}
          {link(tr("st.link.lamekopie"), "https://bias.city/researchtranscript/quellen/lame-4.0.tar.gz")}
        </Flex>
      </Flex>
    </ModalDialog>
  );
}

/** Anzeige oben links statt des App-Namens (User 2026-09-17): der
    Editor meldet den Timecode hh:mm:ss.z, der AI-Tab Laufzeit und
    Schätzung des laufenden Jobs — als Ereignis «rt-kopf» mit fertigem
    Text; sonst eine leere Zeile gleicher Höhe. */
function KopfZeit({ schluessel }: { schluessel: string }) {
  const [text, setText] = useState("");
  useEffect(() => {
    const h = (e: Event) => setText((e as CustomEvent<string>).detail);
    window.addEventListener("rt-kopf", h);
    return () => window.removeEventListener("rt-kopf", h);
  }, []);
  // Tab- oder Editorwechsel: alte Anzeige weg, bis das Modul meldet
  useEffect(() => { setText(""); }, [schluessel]);
  return (
    <Heading size="4" style={{ fontVariantNumeric: "tabular-nums",
                               minWidth: 96, whiteSpace: "nowrap" }}>
      {text || "\u00a0"}
    </Heading>
  );
}

function FirstRun({ onDone }: { onDone: (s: Settings) => void }) {
  const tr = useT();
  const [fehler, setFehler] = useState("");
  const setze = async (root: string) => {
    try {
      onDone(await apiSend<Settings>("/api/settings",
                                     { library_root: root }));
    } catch (e) { setFehler(errMsg(e)); }
  };
  return (
    <Flex align="center" justify="center" direction="column" gap="4"
          style={{ height: "100vh" }}>
      <Icon name="folder" size={40} />
      <Heading size="5">{tr("firstrun.titel")}</Heading>
      <Text size="2" color="gray"
            style={{ maxWidth: 440, textAlign: "center" }}>
        {tr("firstrun.text")}</Text>
      <Flex gap="3">
        {/* In der App (Sandbox) gibt es keinen sichtbaren Standardordner
            ohne Freigabe: der Dialog öffnet im echten ~/Documents, dort
            kann die Person «ResearchTranscript» anlegen oder wählen; die
            Freigabe wird als Bookmark gemerkt. Im Browser wie bisher. */}
        {isTauri() ? (
          <Button size="1" variant="soft" color="gray" highContrast onClick={() => {
            void standardOrdner().then((d) => pickOrdner(d)).then(async (p) => {
              if (!p) return;
              await ordnerMerken(p);
              await setze(p);
            });
          }}>{tr("firstrun.waehlen")}</Button>
        ) : (
          <Button size="1" variant="soft" color="gray" highContrast onClick={() => void setze("default")}>
            {tr("firstrun.standard")}</Button>
        )}
      </Flex>
      {fehler && <Text size="1" color="red">{fehler}</Text>}
    </Flex>
  );
}
