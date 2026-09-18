// Human-Editor (User 2026-08-30): Spiegel des Speicherorts — Liste
// aller Transkripte + „Transkript importieren" (holt vtt/csv UND mp3
// in den Speicherort; Klick öffnet den Editor).
import { useCallback, useEffect, useRef, useState } from "react";
import {
  Button, Checkbox, EmptyState, ErrorNote, Flex, IconButton, ListRow,
  ModalDialog, SuccessNote, Text, TextField,
} from "../components/ui";
import { Icon } from "../components/icons";
import {
  apiGet, apiSend, apiUpload, errMsg, hms, kuerze,
  type EintragMeta,
} from "../lib/api";
import { useT } from "../lib/i18n";
import { isTauri, onFileDrop, pickAudio, pickTranskript, savePath } from "../lib/tauri";

export default function HumanEditorModule({ onOpen }: {
  onOpen: (id: string) => void;
}) {
  const tr = useT();
  const [eintraege, setEintraege] = useState<EintragMeta[]>([]);
  const [fehler, setFehler] = useState("");
  const importRef = useRef<HTMLInputElement>(null);
  // Auswahl für die Begleitdokumente (Methodenbaustein, Datenblatt, Paket):
  // nichts angekreuzt = alle
  const [auswahl, setAuswahl] = useState<Set<string>>(new Set());
  const [dokOffen, setDokOffen] = useState(false);

  const lade = useCallback(async () => {
    try {
      const r = await apiGet<{ transcripts: EintragMeta[] }>(
        "/api/transcripts");
      setEintraege(r.transcripts);
    } catch (e) { setFehler(errMsg(e)); }
  }, []);
  useEffect(() => { void lade(); }, [lade]);
  // Drop auf die Liste: .enrich (Datei oder Package-Ordner), .vtt,
  // .csv — die Shell liefert Pfade, das Backend erkennt die Form.
  useEffect(() => {
    let ab: (() => void) | undefined;
    let weg = false;
    void onFileDrop((pfade) => {
      setFehler("");
      void (async () => {
        for (const p of pfade) {
          if (!/\.(enrich|enrich\.zip|vtt|webvtt|csv)$/i.test(p)) continue;
          try { await apiSend("/api/import-path", { path: p }); }
          catch (e) { setFehler(errMsg(e)); }
        }
        void lade();
      })();
    }).then((f) => { if (weg) f(); else ab = f; });
    return () => { weg = true; ab?.(); };
  }, [lade]);

  const importiere = useCallback(async () => {
    setFehler("");
    try {
      if (isTauri()) {
        const p = await pickTranskript();
        if (!p) return;
        // Ein .enrich (Datei oder Package) trägt sein Audio schon mit
        // sich — nur bei vtt/csv lohnt die Nachfrage (User 2026-09-09).
        const audio = /\.enrich(\.zip)?$/i.test(p)
          ? null : await pickAudio(tr("he.audiowahl"), false);
        await apiSend("/api/import-path", { path: p,
          audio_path: audio?.[0] ?? null });
        void lade();
      } else {
        importRef.current?.click();
      }
    } catch (e) { setFehler(errMsg(e)); }
  }, [lade, tr]);

  return (
    <Flex direction="column" gap="3" p="4"
          style={{ height: "100%", overflowY: "auto" }}>
      <Flex gap="3" align="center" wrap="wrap">
        <Button size="1" variant="soft" color="gray" highContrast onClick={() => void importiere()}>
          <Icon name="text" /> {tr("bib.import")}</Button>
        <Button size="1" variant="soft" color="gray" highContrast
                disabled={eintraege.length === 0} onClick={() => setDokOffen(true)}>
          <Icon name="download" /> {tr("dok.knopf")}
          {auswahl.size > 0 ? ` (${auswahl.size})` : ""}</Button>
        <input ref={importRef} type="file" hidden accept=".vtt,.csv,.enrich,.zip"
               onChange={(e) => {
                 const f = e.target.files?.[0];
                 e.target.value = "";
                 if (!f) return;
                 const fd = new FormData();
                 fd.append("datei", f);
                 void apiUpload("/api/import", fd)
                   .then(() => lade())
                   .catch((err) => setFehler(errMsg(err)));
               }} />
      </Flex>

      {fehler && <ErrorNote>{fehler}</ErrorNote>}

      {eintraege.length === 0
        ? <EmptyState>{tr("he.leer")}</EmptyState>
        : eintraege.map((e) => (
            <EintragZeile key={e.id} e={e} onOpen={onOpen}
                          gewaehlt={auswahl.has(e.id)}
                          onWahl={(an) => setAuswahl((alt) => {
                            const neu = new Set(alt);
                            if (an) neu.add(e.id); else neu.delete(e.id);
                            return neu;
                          })}
                          onChanged={() => void lade()} />
          ))}
      <DokumenteDialog open={dokOffen} onClose={() => setDokOffen(false)}
                       ids={(auswahl.size ? eintraege.filter((e) => auswahl.has(e.id)) : eintraege)
                         .map((e) => e.id)}
                       alle={auswahl.size === 0} />
    </Flex>
  );
}

/** Begleitdokumente für Forschende (backend dokumente.py): Methodenbaustein,
    Repositoriums-Datenblatt, Verfahrensbaustein — einzeln als .md/.docx, die
    Zitierdatei für Zotero, oder alles zusammen als Zip. */
function DokumenteDialog({ open, onClose, ids, alle }: {
  open: boolean; onClose: () => void; ids: string[]; alle: boolean;
}) {
  const tr = useT();
  const [note, setNote] = useState("");
  const [fehler, setFehler] = useState("");
  const [laeuft, setLaeuft] = useState(false);
  useEffect(() => { if (open) { setNote(""); setFehler(""); } }, [open]);
  const erzeuge = async (art: string, format: string) => {
    setNote(""); setFehler("");
    const endung = art === "paket" ? "zip" : art === "zitate" ? "bib" : format;
    try {
      if (isTauri()) {
        const p = await savePath(`${tr(`dok.datei.${art}`)}.${endung}`, endung);
        if (!p) return;
        setLaeuft(true);
        await apiSend("/api/dokument", { art, format, ids, path: p });
        setNote(tr("ed.exportiert", { p }));
      } else {
        window.open(`/api/dokument/${art}?format=${format}&ids=${ids.join(",")}`, "_blank");
      }
    } catch (e) { setFehler(errMsg(e)); }
    finally { setLaeuft(false); }
  };
  const zeile = (art: string, formate: [string, string][]) => (
    <Flex key={art} align="start" gap="3" py="2"
          style={{ borderTop: "1px solid var(--gray-a4)" }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <Text as="div" size="2" weight="medium">{tr(`dok.${art}`)}</Text>
        <Text as="div" size="1" color="gray">{tr(`dok.${art}.text`)}</Text>
      </div>
      <Flex gap="1" style={{ flex: "none" }}>
        {formate.map(([format, label]) => (
          <Button key={format} size="1" variant="soft" color="gray" highContrast
                  disabled={laeuft} onClick={() => void erzeuge(art, format)}>{label}</Button>))}
      </Flex>
    </Flex>
  );
  const md: [string, string][] = [["md", ".md"], ["docx", ".docx"]];
  return (
    <ModalDialog open={open} onOpenChange={(o) => !o && onClose()} title={tr("dok.titel")}
                 footer={<Button size="1" variant="soft" color="gray" highContrast
                                 onClick={onClose}>{tr("allg.schliessen")}</Button>}>
      <Text as="div" size="2">{tr("dok.text")}</Text>
      <Text as="div" size="1" color="gray" mt="1" mb="2">
        {alle ? tr("dok.auswahl.alle", { n: ids.length }) : tr("dok.auswahl.n", { n: ids.length })}</Text>
      {zeile("paket", [["zip", ".zip"]])}
      {zeile("methoden", md)}
      {zeile("repositorium", md)}
      {zeile("verfahren", md)}
      {zeile("zitate", [["bib", ".bib"]])}
      <Text as="div" size="1" color="gray" mt="2">{tr("dok.protokoll.hinweis")}</Text>
      {note && <SuccessNote>{note}</SuccessNote>}
      {fehler && <ErrorNote>{fehler}</ErrorNote>}
    </ModalDialog>
  );
}

function EintragZeile({ e, onOpen, onChanged, gewaehlt, onWahl }: {
  e: EintragMeta; onOpen: (id: string) => void;
  onChanged: () => void;
  gewaehlt: boolean; onWahl: (an: boolean) => void;
}) {
  const tr = useT();
  const [frage, setFrage] = useState<"umbenennen" | "loeschen" | null>(
    null);
  const [name, setName] = useState(e.name);
  const [dialogFehler, setDialogFehler] = useState("");
  return (
    <>
      <ListRow
        leading={
          <span onClick={(ev) => ev.stopPropagation()} onKeyDown={(ev) => ev.stopPropagation()}
                style={{ display: "flex" }}>
            <Checkbox color="gray" highContrast checked={gewaehlt}
                      aria-label={tr("dok.waehlen")}
                      onCheckedChange={(v) => onWahl(v === true)} />
          </span>}
        title={kuerze(e.name, 72)}
        meta={`${hms(e.dauer)} · ${tr("bib.sprecher.n",
          { n: e.sprecher })} · ${tr("bib.segmente.n",
          { n: e.segmente })}`}
        onClick={() => onOpen(e.id)}
        trailing={
          <Flex gap="1" onClick={(ev) => ev.stopPropagation()}>
            <IconButton title={tr("bib.umbenennen")}
                        onClick={() => setFrage("umbenennen")}>
              <Icon name="edit" size={14} /></IconButton>
            <IconButton title={tr("bib.loeschen")}
                        onClick={() => setFrage("loeschen")}>
              <Icon name="trash" size={14} /></IconButton>
          </Flex>
        } />
      <ModalDialog open={frage === "umbenennen"}
                   onOpenChange={(o) => !o && setFrage(null)}
                   title={tr("bib.umbenennen")}
                   footer={
                     <Button size="1" variant="soft" color="gray" highContrast onClick={() => {
                       void apiSend(`/api/transcripts/${e.id}/rename`,
                                    { name })
                         .then(() => { setFrage(null); onChanged(); })
                         .catch((err) => setDialogFehler(errMsg(err)));
                     }}>{tr("allg.ok")}</Button>}>
        <TextField.Root value={name}
                        onChange={(ev) => setName(ev.target.value)} />
        {dialogFehler && (
          <Text size="1" color="red">{dialogFehler}</Text>)}
      </ModalDialog>
      <ModalDialog open={frage === "loeschen"}
                   onOpenChange={(o) => !o && setFrage(null)}
                   title={tr("bib.loeschen")}
                   footer={
                     <Button size="1" variant="soft" color="red" onClick={() => {
                       void apiSend(`/api/transcripts/${e.id}/delete`,
                                    { confirm: e.id })
                         .then(() => { setFrage(null); onChanged(); })
                         .catch((err) => setDialogFehler(errMsg(err)));
                     }}>{tr("bib.loeschen")}</Button>}>
        <Text size="2">{tr("bib.loeschen.text", { name: e.name })}</Text>
        {dialogFehler && (
          <Text size="1" color="red">{dialogFehler}</Text>)}
      </ModalDialog>
    </>
  );
}
