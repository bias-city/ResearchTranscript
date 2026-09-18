"""Testi del pacchetto di documentazione — italiano. Chiavi e segnaposto identici a de.py."""

T = {
    # ---- generale ----
    "feld": "Campo", "wert": "Valore", "datei": "File", "groesse": "Dimensione", "hinweis": "Nota",
    "eintrag": "Voce", "dezimal": ",", "nicht_aufgezeichnet": "non registrato",
    "fuss": "Generato da ResearchTranscript {v} il {datum} per «{name}». I campi aperti `[ … ]` vanno compilati dal gruppo di ricerca.",
    "von": "{n} su {gesamt} ({anteil})",

    # ---- cartelle e nomi dei file (ASCII, minuscolo, trattini) ----
    "paket.ordner": "documentazione", "ordner.methoden": "1-metodi", "ordner.datenschutz": "2-protezione-dei-dati",
    "ordner.ablage": "3-deposito-dei-dati", "ordner.zitieren": "citare",
    "datei.liesmich": "LEGGIMI", "datei.protokoll": "protocollo-di-trascrizione",
    "datei.absatz": "paragrafo-metodi", "datei.tatsachen": "fatti-sull-app",
    "datei.stelle": "indicazioni-del-titolare", "datei.datensatz": "scheda-dataset",
    "datei.interview": "scheda-intervista", "datei.ethik": "lista-etica",
    "datei.repos": "repository-e-requisiti",

    # ---- LEGGIMI ----
    "l.titel": "Pacchetto di documentazione",
    "l.text": "Documenti di accompagnamento di una trascrizione, generati dai valori che l'app conosce. Il pacchetto non contiene né la trascrizione né la registrazione.",
    "l.wofuer": "A che cosa serve",
    "l.zeilen": "{methoden}/{protokoll} :: Come è nata la trascrizione e quanto è stata rivista a mano. Fa parte della documentazione dei dati.\n"
                "{methoden}/{absatz} :: Paragrafo per la sezione metodi, breve ed esteso.\n"
                "{datenschutz}/{tatsachen} :: Che cosa l'app fa e non fa. Per il registro delle attività di trattamento, la valutazione d'impatto sulla protezione dei dati, la domanda alla commissione etica.\n"
                "{datenschutz}/{stelle} :: Ciò che sa solo il titolare del trattamento, come modulo.\n"
                "{ablage}/{datensatz} :: Campi per Zenodo e DataCite, una volta per set di dati.\n"
                "{ablage}/{interview} :: Indicazioni su questa singola intervista.\n"
                "{ablage}/{ethik} :: Punti di verifica prima di una pubblicazione.\n"
                "{ablage}/{repos} :: Quale repository, quali formati, quali requisiti.\n"
                "{zitieren}/researchtranscript.bib :: Software e modelli come voci per Zotero (File › Importa).",
    "l.vorher": "Prima della trasmissione a terzi",
    "l.vorher.punkte": "Il nome della trascrizione, il file di origine e i nomi dei file di questo pacchetto possono nominare persone. Da verificare prima della trasmissione a terzi.\n"
                       "La registrazione audio contiene la voce ed è un dato personale.\n"
                       "Pseudonimizzato non significa anonimizzato. Il diritto in materia di protezione dei dati continua ad applicarsi.\n"
                       "`ausgang.json`, `history/` e la registrazione contengono il testo letterale precedente a una pseudonimizzazione.\n"
                       "I documenti non sono una consulenza giuridica.",

    # ---- 1a Protocollo di trascrizione ----
    "p.titel": "Protocollo di trascrizione",
    "p.einleitung": "Il protocollo documenta come è nata questa trascrizione e quanto è stata rivista a mano. Le indicazioni provengono dalla trascrizione e dal suo giornale.",
    "p.transkript": "Trascrizione", "p.maschine": "Trascrizione automatica", "p.hand": "Revisione manuale",
    "p.eingriff": "Intervento rispetto alla trascrizione automatica", "p.dateien": "File",
    "p.software": "Software e modelli",
    "f.name": "Nome nella biblioteca", "f.quelldatei": "File di origine", "f.dauer": "Durata della trascrizione",
    "f.sprache": "Lingua (impostazione)", "f.segmente": "Segmenti", "f.sprecher": "Parlanti nella versione finale",
    "f.memos": "Memo", "f.zotero": "Zotero", "zotero.ja": "collegato", "zotero.nein": "non collegato",
    "f.datum": "Data dell'elaborazione", "f.app": "App", "f.erkennung": "Riconoscimento vocale",
    "f.vad": "Rilevamento dell'attività vocale", "f.trennung": "Separazione dei parlanti", "f.ort": "Luogo dell'elaborazione",
    "app.vorgaenger": "{name} {version} (nome precedente di ResearchTranscript; la numerazione è ripartita da 0.4.0)",
    "erkennung.wert": "whisper.cpp {whisper}, modello `{modell}` ({herkunft})",
    "erkennung.alt": "whisper.cpp, modello `{modell}`; versione del programma non registrata al momento dell'elaborazione",
    "modell.mitgeliefert": "fornito con l'app", "modell.eigen": "modello proprio del gruppo di ricerca",
    "modell.unbekannt": "provenienza non registrata",
    "vad.an": "Silero VAD {silero} in whisper.cpp", "vad.aus": "non utilizzato",
    "vad.diar": "non utilizzato; i blocchi sono tagliati dalla separazione dei parlanti",
    "diar.aus": "disattivata",
    "diar.an": "SpeakerKit (Argmax); modelli pyannote segmentation-3.0, WeSpeaker ResNet34 e pyannote community-1, convertiti da Argmax in Core ML. Numero di parlanti: {zahl}",
    "diar.auto": "automatico", "diar.schwelle": "soglia di raggruppamento {wert}",
    "ort.neu": "in locale sul Mac; riconoscimento vocale in un programma ausiliario del pacchetto dell'app",
    "ort.alt": "in locale sul Mac",
    "p.importiert": "Questa trascrizione è stata importata da `{datei}`, non trascritta nell'app. Lo stato iniziale è il file così come è arrivato.",
    "f.sitzungen": "Sessioni di revisione", "f.zeitraum": "Periodo", "f.wer": "Rivisto da (sessioni)",
    "f.rolle": "Ruolo di chi ha rivisto", "f.abgehoert": "Riascoltato a confronto con la registrazione",
    "f.regeln": "Regole di trascrizione", "f.pseudonym": "Pseudonimizzazione",
    "sitzungen.text": "{n} (sequenze di salvataggi della stessa installazione con meno di dieci minuti di pausa)",
    "wer.eintrag": "{wer} ({n})", "wer.install": "installazione {kennung}",
    "offen.rolle": "[ … ]", "offen.abgehoert": "[ integralmente / in parte / no ]",
    "offen.regeln": "[ … ] (p. es. Dresing & Pehl, sistema semplice o esteso)",
    "offen.pseudonym": "[ … ] (che cosa è stato sostituito, secondo quale regola)",
    "e.journal": "Secondo il giornale, per segmento",
    "e.journal.text": "Il giornale annota per ogni sessione quali segmenti sono stati modificati. Si contano i segmenti distinti; se un segmento ha più modifiche in una sessione, vale l'ultima. Le quote sono perciò valori minimi.",
    "e.j.text": "Testo modificato", "e.j.sprecher": "Parlante riassegnato", "e.j.zeit": "Tempo modificato",
    "e.j.summe": "Segmenti con almeno una modifica",
    "e.j.weitere": "Inoltre: {neu} voci create, {weg} rimosse, {name} parlanti rinominati.",
    "e.wort": "Rispetto allo stato iniziale automatico, per parola",
    "e.wort.fehlt": "Per questa trascrizione un tasso per parola non è calcolabile. È nata con una versione che non conservava ancora lo stato grezzo automatico.",
    "e.wort.verlauf": "Lo stato iniziale proviene dallo stato non rivisto più vecchio della cronologia.",
    "mass.kopf": "Misura", "mass.basis": "Base",
    "mass.norm": "Tasso di correzione, normalizzato", "mass.orth": "Tasso di correzione, ortografico",
    "mass.sdi": "{s} sostituite, {d} eliminate, {i} inserite; {n} parole nella versione finale",
    "mass.sprechzeit": "Tempo di parola riassegnato",
    "mass.sprechzeit.basis": "tempo di parola coperto da entrambi gli stati {zeit}; {a} parlanti nello stato iniziale, {b} nella versione finale",
    "mass.mehrheit": "di cui senza parlanti unificati",
    "mass.mehrheit.text": "l'unificazione di due voci qui non conta",
    "mass.ohne_maschine": "la macchina non ha assegnato parlanti",
    "mass.definition": "Tasso di correzione = (parole sostituite + eliminate + inserite) ÷ parole della versione finale. Si conta come per il tasso di errore sulle parole, con la versione finale come riferimento, allineando segmento per segmento. *Normalizzato*: in minuscolo, senza punteggiatura né caratteri speciali. *Ortografico*: come scritto. Tempo di parola riassegnato = quota del tempo di parola coperto da entrambi gli stati con un parlante diverso, con la migliore corrispondenza uno a uno possibile.",
    "mass.vorbehalt": "Misura dell'intervento, non misura della precisione. Conta ogni modifica a mano, anche pseudonimizzazione e levigatura del testo. Non coglie gli errori non notati.",
    "dateien.text": "File nella cartella della trascrizione, con SHA-256.",
    "dateien.ausgang": "`ausgang.json` è lo stato iniziale inalterato. Contiene il testo letterale precedente a una pseudonimizzazione.",
    "software.punkte": "whisper.cpp (MIT): <https://github.com/ggml-org/whisper.cpp>\n"
                       "Whisper large-v3-turbo (OpenAI, MIT): <https://huggingface.co/openai/whisper-large-v3-turbo>\n"
                       "SpeakerKit, Argmax OSS (MIT): <https://github.com/argmaxinc/argmax-oss-swift>\n"
                       "pyannote speaker-diarization-community-1 (CC BY 4.0): <https://huggingface.co/pyannote/speaker-diarization-community-1>\n"
                       "Silero VAD (MIT): <https://github.com/snakers4/silero-vad>\n"
                       "ResearchTranscript (AGPL-3.0-or-later): <https://github.com/bias-city/ResearchTranscript>",

    # ---- 1b Paragrafo sui metodi ----
    "a.titel": "Paragrafo per la sezione metodi",
    "a.einleitung": "Da riprendere e adattare. Le parentesi quadre vanno sostituite. Il paragrafo vale per questa singola trascrizione.",
    "a.kurz": "Versione breve", "a.lang": "Versione estesa, per l'appendice o il piano di gestione dei dati",
    "a.app.neu": "ResearchTranscript {version}", "a.app.alt": "{name} {version} (oggi ResearchTranscript)",
    "a.s1": "La registrazione (durata {dauer}) è stata trascritta con {app} in locale [ su un computer del gruppo di ricerca ]; l'app non trasmette dati.",
    "a.s2": "Il riconoscimento vocale ha usato whisper.cpp con il modello {modell}.",
    "a.s3": "I parlanti sono stati separati da SpeakerKit con modelli pyannote.",
    "a.s4": "La trascrizione grezza è stata verificata [ da chi ] [ integralmente / a campione ] a confronto con la registrazione e corretta secondo [ regole di trascrizione ] [ e pseudonimizzata nel testo ].",
    "a.s5.wort": "Il tasso di correzione a livello di parola è stato pari a {norm} (normalizzato, versione finale come riferimento){sprechzeit}.",
    "a.s5.sprechzeit": "; la quota di tempo di parola riassegnato a mano è stata pari a {wert}",
    "a.s5.journal": "Secondo il giornale, la quota dei segmenti con testo modificato è pari ad almeno {text}, quella dei segmenti con parlante riassegnato a {sprecher}.",
    "a.s6": "I valori misurano l'intervento, non la precisione.",
    "a.k1": "La registrazione è stata trascritta in locale con {app} (whisper.cpp, modello {modell}), poi verificata a confronto con la registrazione e corretta [ da chi ].",
    "a.offen": "Ancora da completare",
    "a.offen.punkte": "Chi ha corretto e se il riascolto è stato integrale.\n"
                      "Secondo quali regole di trascrizione si è lavorato.\n"
                      "Che cosa è stato pseudonimizzato e secondo quale regola.",
    "a.zitieren": "Citare",
    "a.zitieren.text": "Pohl, B. ({jahr}). ResearchTranscript (Versione {v}) [Software]. B/IAS – Basel Institut für angewandte Stadtforschung. <https://bias.city/researchtranscript/> Il file `researchtranscript.bib` nella cartella `{zitieren}` contiene questa voce e i modelli per Zotero.",

    # ---- 2a Fatti sull'app ----
    "t.titel": "ResearchTranscript: fatti per la protezione dei dati e la domanda alla commissione etica",
    "t.einleitung": "Fatti sull'app, da riprendere in un registro delle attività di trattamento, in una valutazione d'impatto sulla protezione dei dati o in una domanda alla commissione etica. Uguali per tutte le trascrizioni. Vale per ResearchTranscript {v}; come è nata un'elaborazione precedente è indicato nel protocollo di trascrizione.",
    "t.schritte": "Che cosa fa l'app con una registrazione", "t.schritt": "Fase", "t.werkzeug": "Strumento", "t.wo": "Dove",
    "t.schritte.zeilen": "Lettura della traccia audio, conversione a 16 kHz mono :: macOS AVFoundation :: in locale, nell'app\n"
                         "Separazione dei parlanti, disattivabile :: SpeakerKit (Argmax) con modelli pyannote e WeSpeaker, Core ML :: in locale, nell'app\n"
                         "Riconoscimento vocale :: whisper.cpp {whisper}, modello a scelta; senza separazione dei parlanti con Silero VAD {silero} :: in locale, programma ausiliario del pacchetto dell'app, unità grafica\n"
                         "Correzione nell'editor, con cronologia e giornale :: ResearchTranscript :: in locale\n"
                         "Esportazione in formati di testo, di tabella e di archivio; MP3 tramite LAME :: ResearchTranscript :: in locale, nella cartella scelta",
    "t.schutz": "Misure di protezione offerte dall'app",
    "t.schutz.punkte": "App Sandbox di macOS: accesso solo alle cartelle che la persona sceglie nella finestra di dialogo e ai file trascinati nell'app.\n"
                       "Nessun server, nessuna porta aperta, nessun account.\n"
                       "Salvataggio in un unico passaggio; prima di ogni salvataggio uno stato nella cronologia (30 stati).\n"
                       "L'eliminazione sposta nel cestino della biblioteca, nulla va perso subito.\n"
                       "Giornale per ogni trascrizione: chi (identificativo dell'installazione, facoltativamente e-mail) ha modificato che cosa e quando.\n"
                       "Zotero viene solo letto, solo dopo l'attivazione.\n"
                       "Codice sorgente aperto, app firmata.",
    "t.nicht": "Che cosa l'app non fa",
    "t.nicht.punkte": "Non trasmette registrazioni, testi o dati di utilizzo: nessuna telemetria, nessuna verifica di aggiornamenti, nessun rapporto di arresto anomalo proprio. L'autorizzazione di rete di macOS è impostata perché la vista web integrata la richiede; un firewall mostra che non nasce alcuna connessione. I rapporti di arresto anomalo di macOS seguono le impostazioni di sistema.\n"
                      "Non scarica a posteriori né modelli né parti di programma.\n"
                      "I modelli non imparano dalle registrazioni.\n"
                      "Non riassume e non riformula nulla. Il riconoscimento vocale è un modello di IA e può inserire parole che non sono state dette; perciò si verifica a confronto con la registrazione.",
    "t.ablage": "Dove si trovano i dati",
    "t.ablage.punkte": "Nella cartella della biblioteca scelta, una sottocartella per trascrizione: `transkript.json` (testo letterale, parlanti, memo, giornale, dati Zotero), una copia della registrazione, per i video il file video, `wellenform.json`.\n"
                       "`ausgang.json` conserva lo stato così come lo ha fornito la macchina o un file importato. `history/` conserva gli ultimi 30 stati. Entrambi contengono il testo letterale precedente a una pseudonimizzazione.\n"
                       "Le trascrizioni eliminate restano nella cartella `_papierkorb` finché questa non viene svuotata nel Finder.\n"
                       "Durante un'elaborazione le copie di lavoro dell'audio si trovano nella cartella temporanea dell'app.\n"
                       "Impostazioni e registro dell'app si trovano nel contenitore dell'app dell'account utente. Il registro contiene marche temporali, comandi, nomi di cartelle e di file e messaggi di errore.",
    "t.person": "Che cosa l'app memorizza sulle persone che fanno ricerca",
    "t.person.punkte": "Un identificativo dell'installazione casuale, senza legame con il dispositivo o la persona.\n"
                       "Facoltativamente un indirizzo e-mail. Entrambi figurano nel giornale di ogni trascrizione e accompagnano il dossier enrich.",
    "t.export": "Che cosa contengono le esportazioni",
    "t.export.punkte": "Tutti i formati di testo (VTT, CSV, TXT, Markdown, Word): testo letterale, nomi dei parlanti, marche temporali. CSV, Markdown e Word in più i memo.\n"
                       "Markdown e Word: con un collegamento Zotero, un'intestazione con titolo, data, citekey e le persone di cui sono stati scelti i ruoli.\n"
                       "REFI-QDA (`.qdpx.zip`): testo, memo e la registrazione audio, quindi la voce; su richiesta il file video.\n"
                       "Dossier enrich (`.enrich`): testo, registrazione audio in MP3, giornale con identificativo ed e-mail, dati Zotero. Nessun memo.",

    # ---- 2b Indicazioni del titolare ----
    "s.titel": "Indicazioni del titolare del trattamento",
    "s.einleitung": "L'app non può conoscere queste indicazioni. Senza di esse una voce nel registro delle attività di trattamento è incompleta.",
    "s.felder": "Titolare del trattamento :: istituzione, direzione del progetto, contatto\n"
                "Consulenza per la protezione dei dati :: persona o servizio competente\n"
                "Scopo :: progetto di ricerca, domanda di ricerca\n"
                "Base giuridica, diritto applicabile :: a seconda dell'ente, diritto cantonale, diritto federale o RGPD\n"
                "Persone interessate :: persone intervistate, terzi menzionati, le ricercatrici e i ricercatori stessi (giornale)\n"
                "Categorie di dati personali :: voce, dichiarazioni, eventualmente dati personali degni di particolare protezione\n"
                "Destinatari :: chi riceve registrazioni, trascrizioni o esportazioni\n"
                "Comunicazione all'estero :: nessuna da parte dell'app; possibile con la trasmissione a terzi o l'archiviazione nel cloud\n"
                "Conservazione e cancellazione :: termini, anche per cestino, cronologia, stato iniziale, backup\n"
                "Ubicazione della biblioteca :: disco interno, unità cifrata, unità di rete\n"
                "Backup e sincronizzazione :: Time Machine, iCloud Drive e altri includono la cartella, se si trova lì\n"
                "Protezione del dispositivo :: FileVault, blocco dello schermo, account utente separati\n"
                "Persone autorizzate all'accesso :: chi lavora al computer e nella cartella\n"
                "Informazione e consenso :: coprono registrazione, trascrizione, conservazione, trasmissione a terzi",
    "s.achten": "A che cosa prestare attenzione",
    "s.achten.punkte": "«In locale» è una proprietà dell'app, non del luogo di archiviazione. Una cartella sincronizzata trasmette i dati.\n"
                       "Viene pseudonimizzato il testo della versione finale. Registrazione, stato iniziale e cronologia continuano a contenere la voce e i nomi reali.\n"
                       "I modelli propri del gruppo di ricerca non fanno parte dell'elenco documentato dell'app.",
    "s.entfernen": "Rimuovere completamente un'intervista",
    "s.entfernen.text": "Per esempio dopo una revoca. L'app non cancella nulla in modo definitivo; questi luoghi vanno verificati uno per uno.",
    "s.entfernen.punkte": "Eliminare la trascrizione nell'app, poi svuotare nel Finder la cartella `_papierkorb` della biblioteca e il cestino di macOS.\n"
                          "Le esportazioni in tutti i luoghi in cui sono state salvate o trasmesse.\n"
                          "Backup e copie sincronizzate della cartella della biblioteca.\n"
                          "La registrazione originale fuori dalla biblioteca.\n"
                          "Per rimuovere solo il testo letterale precedente alla pseudonimizzazione si eliminano `ausgang.json` e `history/`. Dopo, una misura dell'intervento per parola non è più calcolabile.",

    # ---- 3 Deposito dei dati ----
    "r.status": "Stato", "r.st.pflicht": "obbligatorio", "r.st.empfohlen": "consigliato", "r.st.optional": "facoltativo",
    "r.vorschlag": "proposta da Zotero, da verificare",
    "d.titel": "Scheda: indicazioni sul set di dati",
    "d.einleitung": "Da compilare una volta per set di dati, anche se comprende più interviste. Ordine e nomi dei campi seguono il modulo di Zenodo; lo stato si riferisce a Zenodo e DataCite 4.",
    "d.zeilen": "Resource type :: pflicht :: Dataset :: Trascrizioni con la documentazione.\n"
                "Title :: pflicht :: [ … ] :: Descrittivo, senza nomi di persone intervistate.\n"
                "Publication date :: pflicht :: [ … ] :: Data della pubblicazione, non dell'intervista.\n"
                "Creators :: pflicht :: {creators} :: Le ricercatrici e i ricercatori con ORCID e istituzione. Mai le persone intervistate.\n"
                "Description :: empfohlen :: [ … ] :: Di che cosa si tratta, chi è stato intervistato (in termini generali), a quale scopo.\n"
                "Licence :: pflicht :: [ … ] :: Su Zenodo obbligatoria per i file aperti. Per i file sensibili un contratto d'uso al posto di una licenza aperta.\n"
                "Access :: pflicht :: [ … ] :: Su Zenodo vale per ogni voce. Documentazione aperta e trascrizioni ad accesso chiuso come voci separate e collegate.\n"
                "Contributors :: empfohlen :: [ … ] :: Ruoli secondo DataCite, p. es. ContactPerson, DataCollector, RightsHolder.\n"
                "Keywords :: empfohlen :: [ … ] :: Da tre a otto termini, possibilmente tratti da un vocabolario disciplinare.\n"
                "Languages :: optional :: {sprachen} :: Codice ISO della lingua dell'intervista.\n"
                "Dates (Collected) :: empfohlen :: [ … ] :: Periodo della raccolta dei dati. Nel dubbio solo l'anno.\n"
                "Version :: optional :: 1.0 :: Dopo le correzioni una nuova versione.\n"
                "Funding :: optional :: [ … ] :: Ente finanziatore e numero del sussidio.\n"
                "Related works :: empfohlen :: {dois} :: DOI degli articoli che si basano sui dati.",
    "d.befragte": "Le persone della parte intervistata presenti in Zotero sono volutamente omesse.",
    "d.archiv": "Gli archivi specializzati chiedono inoltre",
    "d.archiv.punkte": "Metodo di raccolta dei dati, p. es. intervista guidata da una traccia.\n"
                       "Popolazione di riferimento e selezione delle persone intervistate.\n"
                       "Materiale di accompagnamento: traccia d'intervista, foglio informativo, modello di consenso, rapporto metodologico.",
    "i.titel": "Scheda: indicazioni su questa intervista",
    "i.einleitung": "Ciò che l'app sa di questa singola intervista e ciò che serve in più per il deposito.",
    "i.umfang": "Estensione", "i.umfang.wert": "Durata {dauer}, {segmente} segmenti, {sprecher} parlanti",
    "i.sprache": "Lingua", "i.jahr": "Anno della raccolta dei dati", "i.verfahren": "Procedimento di trascrizione",
    "i.verfahren.wert": "{app}, whisper.cpp, modello {modell}; in locale; rivista a mano (vedi il protocollo di trascrizione)",
    "i.konventionen": "Convenzioni di trascrizione",
    "i.konventionen.wert": "Marche temporali hh:mm:ss per ogni enunciato, parlante come indicazione separata; [ completare le regole ]",
    "i.pseudonym": "Pseudonimizzazione", "i.pseudonym.wert": "[ … ] (la tabella di corrispondenza degli pseudonimi non viene mai depositata)",
    "i.formate": "File per il deposito",
    "i.formate.punkte": "Trascrizione in un formato di testo aperto (TXT, Markdown, CSV), oltre che in Word e REFI-QDA. Calcolare le somme di controllo dopo l'esportazione.\n"
                        "REFI-QDA è un formato di scambio con possibili perdite tra un programma e l'altro, non un formato di archiviazione da usare da solo.\n"
                        "Come versione d'archivio della registrazione serve il file originale, non ricodificato. L'MP3 nei pacchetti dell'app è una copia d'uso.\n"
                        "L'intestazione dell'esportazione Markdown e Word nomina le persone scelte in Zotero. Da verificare prima del deposito.\n"
                        "Il protocollo di trascrizione può essere allegato. `ausgang.json` e `history/` restano fuori.",
    "e.titel": "Punti di verifica prima di una pubblicazione",
    "e.einleitung": "Solo il gruppo di ricerca può rispondere a questi punti. Ciò che non è pertinente va annotato come tale.",
    "e.punkt": "Punto di verifica", "e.ja": "soddisfatto", "e.nz": "non pertinente",
    "e.punkte": "Il consenso copre l'archiviazione e il riutilizzo. :: Altrimenti consultare la commissione etica o la consulenza per la protezione dei dati.\n"
                "Il consenso copre la trasmissione della registrazione audio. :: La voce è un dato personale.\n"
                "Esiste un parere della commissione etica. :: Indicare numero e organo.\n"
                "Caratteristiche dirette e indirette e terzi menzionati sono stati verificati. :: Attenzione a combinazioni come professione, luogo ed età.\n"
                "Titolo, descrizione, parole chiave e nomi dei file non nominano persone. :: Su Zenodo i metadati sono sempre pubblici.\n"
                "La tabella di corrispondenza degli pseudonimi è conservata separatamente. :: Non va mai depositata.\n"
                "Il repository è adatto ai dati. :: Per i dati sensibili un archivio specializzato con controllo degli accessi.\n"
                "I requisiti dell'ente finanziatore e della scuola universitaria sono stati verificati. :: Motivare nel piano di gestione dei dati le eccezioni all'accesso aperto.",
    "o.titel": "Repository, formati, requisiti",
    "o.einleitung": "Uguali per tutte le trascrizioni. Le indicazioni non sostituiscono la consulenza dell'archivio.",
    "o.zenodo": "Che cosa esige Zenodo",
    "o.zenodo.punkte": "I dati personali sensibili, prima di una diffusione aperta, devono essere adeguatamente anonimizzati o coperti da un consenso. Per i dati sensibili non anonimizzati Zenodo rimanda a piattaforme specializzate. La responsabilità è di chi carica i file.\n"
                       "I metadati sono sempre pubblici, anche quando i file sono ad accesso chiuso.\n"
                       "Una voce DOI pubblicata non si può cancellare senza lasciare traccia.\n"
                       "Limiti: 50 GB e 100 file per voce.",
    "o.repos": "Repository", "o.repo": "Repository", "o.fuer": "Idoneità",
    "o.repos.zeilen": "Zenodo :: Generalista, DOI immediato. Per documentazione, strumenti e testi davvero anonimizzati, non per le registrazioni. :: https://zenodo.org\n"
                      "SWISSUbase :: Svizzera. Accetta dati qualitativi e sensibili, con controllo degli accessi e contratto d'uso. DOI. :: https://www.swissubase.ch\n"
                      "Qualiservice :: Germania, dati qualitativi. Consulenza, aiuto per l'anonimizzazione, accesso su richiesta. DOI. :: https://www.qualiservice.org\n"
                      "AUSSDA :: Austria, scienze sociali. Direttiva propria per i dati qualitativi. :: https://aussda.at\n"
                      "UK Data Service :: Regno Unito. Accesso graduato. :: https://ukdataservice.ac.uk",
    "o.vorgaben": "Requisiti e guide",
    "o.vorgaben.punkte": "Zenodo, campi: <https://help.zenodo.org/docs/deposit/describe-records/>\n"
                         "Zenodo, linee guida e condizioni: <https://about.zenodo.org/policies/> · <https://about.zenodo.org/terms/>\n"
                         "DataCite Metadata Schema 4: <https://schema.datacite.org>\n"
                         "SWISSUbase e FORS, depositare i dati: <https://forscenter.ch/deposit-data/>\n"
                         "FORS Guide n. 20, anonimizzazione di dati qualitativi: <https://doi.org/10.24449/FG-2023-00020>\n"
                         "Qualiservice, condividere i dati: <https://www.qualiservice.org/de/daten-teilen.html>\n"
                         "CESSDA Data Management Expert Guide: <https://dmeg.cessda.eu>\n"
                         "FNS, Open Research Data: <https://www.snf.ch/de/FAiWVH4WvpKvohw9/thema/forschungsdaten>\n"
                         "DFG, gestione dei dati di ricerca: <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>\n"
                         "Modello di README della Cornell University (CC0): <https://data.research.cornell.edu/data-management/sharing/readme/>",
}
