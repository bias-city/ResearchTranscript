# Begleitdokumente für Forschende — Zuschnitt und Grundlagen

Stand 18.9.2026, ResearchTranscript 0.6.0. Gehört zu BACKLOG 16. Code:
`backend/src/researchtranscript/{eingriff,dokumente,docx}.py`, Texte in
`dokumente_texte/<sprache>.py` (de = Quelle).

## Was die App erzeugt

| Dokument | Ebene | Wo in der App | Warum diese Ebene |
|---|---|---|---|
| Transkript als `.md` / `.docx` | je Transkript | Editor › Export | Lesefassung mit Kopf (Kennung, Datum, Kontext), wie CESSDA und UK Data Service ihn je Transkript verlangen |
| Transkriptionsprotokoll | je Transkript | Editor › Export | Provenienz ist Objektebene der Datendokumentation (CESSDA DMEG) |
| Methodenbaustein | Auswahl 1…n | Bibliothek › Dokumentation | Ein Methodenteil beschreibt das Korpus; JARS-Qual verlangt Mittelwert und Spanne der Dauer |
| Verfahrensbaustein | Projekt | Bibliothek › Dokumentation | DSGVO Art. 30 und DSG Art. 12 führen Tätigkeiten, nicht Aufnahmen; Art. 22 DSG erlaubt eine gemeinsame DSFA für ähnliche Vorgänge |
| Repositoriums-Datenblatt | Auswahl 1…n | Bibliothek › Dokumentation | Ein Datensatz mit DOI umfasst meist mehrere Interviews |
| Zitierdatei `.bib` | App | Bibliothek › Dokumentation | Software als zitierbarer Eintrag (Zotero «Software»); dazu `CITATION.cff` im Repo |
| Dokumentationspaket `.zip` | Auswahl | Bibliothek › Dokumentation | alles oben, je `.md` und `.docx` |

Verworfen: eine «Verfahrensbeschreibung» je Transkript (erste Idee) — sie
passt zu keiner der Stellen, die solche Texte verlangen.

## Eingriffsmass

Grundlage ist `ausgang.json` je Transkript: der Stand, wie ihn die Maschine
(oder eine importierte Datei) lieferte. Geschrieben beim Anlegen; für
Einträge von vor 0.6.0 beim ersten Eingriff nachgeholt, sonst aus dem
ältesten unberührten Stand in `history/`; fehlt beides, nennt das Protokoll
nur den Anteil der Segmente mit `origin: human`.

- **Korrekturrate Wortebene** = (S + D + I) ÷ Wörter der Endfassung —
  gerechnet wie die WER mit der Endfassung als Referenz; dieselbe
  Konstellation wie HTER in der Post-Editing-Forschung (Snover et al. 2006).
  *Normalisiert* (klein, ohne Satz-/Sonderzeichen, Diakritika bleiben) und
  *orthografisch*. Ohne Angabe der Normalisierung sind solche Raten nicht
  vergleichbar (Whisper-Normalizer und jiwer-Standard unterscheiden sich).
- **Neu zugeordnete Sprechzeit** = Anteil der Sprechzeit mit anderem Sprecher
  als im Ausgangsstand, bestmögliche 1:1-Zuordnung, ohne Toleranzfenster —
  die Verwechslungskomponente der DER (pyannote.metrics). Zusätzlich die
  Lesart mit Mehrheitszuordnung: ein Zusammenführen zweier Stimmen zählt
  dort nicht je Stelle.
- Nie «Fehlerrate» oder «Genauigkeit»: die Endfassung ist nach
  Pseudonymisierung und Glättung kein Verbatim-Goldstandard, und unbemerkte
  Fehler erfasst die Rate nicht.
- Gerechnet wird über eine Diff-Karte der Segment-IDs: exakt nur dort, wo
  etwas geschah (30 000 Wörter in Bruchteilen einer Sekunde).

## Was die Dokumente nie behaupten

Verantwortliche Stelle, Rechtsgrundlage, anwendbares Recht (kantonal, Bund,
DSGVO), Einwilligung, Fristen, Speicherort, Backups und Synchronisation,
Geräteschutz, wer korrigiert hat. «Lokal» ist eine Eigenschaft der App,
nicht des Ordners. Nie «anonymisiert», nie «DSGVO-konform». Befragte aus
Zotero (Rollen interviewee, guest, castMember, author) erscheinen nie als
Urheber. Hinweis in allen Dokumenten: Aufnahme, `ausgang.json` und
`history/` enthalten den Wortlaut VOR einer Pseudonymisierung.

## Quellen (am Primärtext geprüft, 18.9.2026)

- DSGVO Art. 30 <https://gdpr-info.eu/art-30-gdpr/> · DSG SR 235.1 Art. 12, 22 <https://www.fedlex.admin.ch/eli/cc/2022/491/de>
- CESSDA DMEG, Dokumentation <https://dmeg.cessda.eu/Data-Management-Expert-Guide/2.-Organise-Document/Documentation-and-metadata>, Anonymisierung <https://dmeg.cessda.eu/Data-Management-Expert-Guide/5.-Protect/Anonymisation>, Formate <https://dmeg.cessda.eu/Data-Management-Expert-Guide/3.-Process/File-formats-and-data-conversion>
- APA JARS-Qual <https://apastyle.apa.org/jars/qual-table-1.pdf>
- Wollin-Giering et al. 2024 <https://doi.org/10.17169/fqs-25.1.4129> · Eftekhari 2024 <https://doi.org/10.1093/eurjcn/zvae013>
- WER <https://en.wikipedia.org/wiki/Word_error_rate> · Whisper-Normalizer <https://github.com/openai/whisper/blob/main/whisper/normalizers/basic.py> · jiwer <https://jitsi.github.io/jiwer/reference/transformations/> · HTER <https://aclanthology.org/2006.amta-papers.25/> · DER <https://pyannote.github.io/pyannote-metrics/reference.html>
- Zenodo: Felder <https://help.zenodo.org/docs/deposit/describe-records/>, Dateien <https://help.zenodo.org/docs/deposit/manage-files/>, Policies <https://about.zenodo.org/policies/>, Terms <https://about.zenodo.org/terms/> · InvenioRDM-Metadaten <https://inveniordm.docs.cern.ch/reference/metadata/>
- DataCite 4.7 <https://datacite-metadata-schema.readthedocs.io/en/4.7/properties/overview/>
- FORS / SWISSUbase <https://forscenter.ch/deposit-data/>, FORS Guide 20 <https://doi.org/10.24449/FG-2023-00020> · Qualiservice <https://www.qualiservice.org/de/daten-teilen.html> · UK Data Service <https://ukdataservice.ac.uk/learning-hub/data-producer-support/preparing-data-for-sharing-and-reuse/documenting-and-describing-data/data-leveldocumentation/> · AUSSDA <https://aussda.at/en/deposit-data/>
- SNF ORD <https://www.snf.ch/en/dMILj9t4LNk8NwyR/topic/open-research-data> · DFG <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>

Nicht am Primärtext geprüft (nur bibliografisch): COREQ, SRQR, ICML-Fassung
des Whisper-Papers, Details der Wespeaker- und VBx-Zitate. Die App zitiert
darum Radford et al. als arXiv-Fassung und nennt COREQ/SRQR nicht.
