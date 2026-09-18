"""Testi dei documenti di accompagnamento — italiano. Chiavi e segnaposto identici a de.py."""

T = {
    # ---- generale ----
    "feld": "Campo", "wert": "Valore", "datei": "File", "groesse": "Dimensione", "nachweise": "Riferimenti",
    "nicht_aufgezeichnet": "non registrato", "dezimal": ",",
    "kopf.erzeugt": "Generato da ResearchTranscript {v} il {datum}. I campi aperti sono contrassegnati con `[ … ]` "
                    "e vanno compilati dalle ricercatrici e dai ricercatori.",
    "modell.mitgeliefert": "fornito con l'app", "modell.eigen": "modello proprio del gruppo di ricerca",
    "modell.unbekannt": "provenienza non registrata",
    "modell.heute": "— provenienza secondo lo stato attuale dell'installazione, non registrata al momento dell'elaborazione",
    "diar.aus": "nessuna (disattivata)", "diar.an": "SpeakerKit (Argmax) con pyannote community-1, Core ML",
    "diar.auto": "automatico", "diar.zahl": "numero di parlanti:", "diar.trennung": "soglia di raggruppamento",
    "vad.aus": "non utilizzato", "ort.lokal": "in locale sul Mac, nel processo dell'app; nessuna trasmissione da parte dell'app",

    "f.kennung": "Identificativo", "f.name": "Nome nella biblioteca", "f.quelldatei": "File di origine",
    "f.dauer": "Durata", "f.sprache": "Lingua (impostazione)", "f.segmente": "Segmenti",
    "f.sprecher": "Parlanti (numero)", "f.memos": "Memo (numero)", "f.datum": "Data dell'elaborazione",
    "f.app": "Software", "f.erkennung": "Riconoscimento vocale", "f.modell": "Modello", "f.modell.satz": "modello",
    "f.vad": "Rilevamento dell'attività vocale", "f.trennung": "Separazione dei parlanti", "f.ort": "Luogo dell'elaborazione",
    "f.sitzungen": "Sessioni di modifica secondo il giornale", "f.zeitraum": "Periodo delle modifiche",
    "f.journal": "Voci modificate secondo il giornale", "f.wer": "Modificato da",
    "f.abgehoert": "Riascoltato a confronto con la registrazione", "f.regeln": "Regole di trascrizione",
    "f.pseudonym": "Pseudonimizzazione",
    "journal.arten": "testo {text} · assegnazione del parlante {sprecher} · tempo {zeit} · nuovi {neu} · rimossi {weg} · "
                     "parlanti rinominati {name}",
    "offen.wer": "[ … ] (nome o ruolo; l'app non lo registra)",
    "offen.abgehoert": "[ integralmente / in parte / no ]",
    "offen.regeln": "[ … ] (p. es. Dresing & Pehl, sistema semplice o esteso; regole proprie)",
    "offen.pseudonym": "[ … ] (che cosa è stato sostituito e secondo quale regola; la tabella di corrispondenza degli "
                       "pseudonimi è conservata separatamente)",

    # ---- pacchetto di documentazione ----
    "paket.ordner": "researchtranscript-documentazione", "paket.liesmich": "LEGGIMI",
    "paket.protokolle": "protocolli", "paket.titel": "Pacchetto di documentazione",
    "paket.text": "Documenti di accompagnamento delle trascrizioni scelte, ciascuno in Markdown e come file Word. "
                  "I campi aperti `[ … ]` vanno compilati dalle ricercatrici e dai ricercatori. Il pacchetto non "
                  "contiene né trascrizioni né registrazioni.",
    "paket.bib": "File di citazione per Zotero (File › Importa): il software e tutte le fonti citate",

    # ---- 1. Protocollo di trascrizione ----
    "datei.protokoll": "protocollo-di-trascrizione",
    "p.titel": "Protocollo di trascrizione",
    "p.einleitung": "Questo protocollo documenta come è nata la trascrizione e in quale misura è stata modificata a "
                    "mano. Fa parte della documentazione del singolo oggetto di dati e può essere allegato al "
                    "pacchetto di dati. Le indicazioni provengono dal giornale della trascrizione; il protocollo non "
                    "riporta nomi di parlanti.",
    "p.aufnahme": "Registrazione e trascrizione", "p.maschine": "Trascrizione automatica",
    "p.importiert": "Questa trascrizione non è stata prodotta nell'app, ma importata da `{datei}`. "
                    "Lo stato iniziale è il file così come è arrivato.",
    "p.hand": "Modifica a mano", "p.mass": "Misura dell'intervento", "p.dateien": "File",
    "dateien.hinweis": "File nella cartella della trascrizione, con somma di controllo. `ausgang.json` è lo stato "
                       "iniziale inalterato, rispetto al quale si calcola la misura dell'intervento.",

    "mass.kopf.mass": "Misura", "mass.kopf.basis": "Base",
    "mass.norm": "Tasso di correzione a livello di parola, normalizzato",
    "mass.orth": "Tasso di correzione a livello di parola, ortografico",
    "mass.sdi": "{s} sostituite, {d} eliminate, {i} inserite; {n} parole nella versione finale",
    "mass.sprechzeit": "Tempo di parola riassegnato",
    "mass.sprechzeit.basis": "tempo di parola confrontato {zeit}; {a} parlanti nello stato iniziale, {b} nella versione finale",
    "mass.sprechzeit.mehrheit": "di cui senza parlanti unificati",
    "mass.sprechzeit.mehrheit.text": "ammessa l'assegnazione di più parlanti della macchina alla stessa persona: "
                                     "l'unificazione di due voci qui non conta",
    "mass.ohne_maschine": "la macchina non ha assegnato parlanti; tutte le assegnazioni sono state fatte a mano",
    "mass.fehlt": "Per questa trascrizione non esiste più uno stato iniziale (creata prima della versione 0.6.0, la "
                  "cronologia non risale abbastanza indietro). Un tasso di correzione non è calcolabile. A titolo "
                  "indicativo: {n} segmenti su {gesamt} ({anteil}) portano l'annotazione «modificato a mano».",
    "mass.aus_verlauf": "Lo stato iniziale proviene dallo stato più vecchio della cronologia che nessuno aveva ancora modificato.",
    "mass.definition": "**Definizioni.** Tasso di correzione = (parole sostituite + eliminate + inserite) ÷ parole della "
                       "versione finale, calcolato come il tasso di errore sulle parole (WER), con la versione finale "
                       "come riferimento e lo stato iniziale come ipotesi. *Normalizzato*: in minuscolo, senza segni "
                       "di punteggiatura né caratteri speciali; dieresi e accenti restano. *Ortografico*: parole così "
                       "come sono scritte; maiuscole, minuscole e punteggiatura contano. Tempo di parola riassegnato = "
                       "quota del tempo di parola il cui parlante nella versione finale è diverso da quello dello "
                       "stato iniziale, con la migliore corrispondenza uno a uno possibile tra i parlanti; corrisponde "
                       "alla componente di confusione del Diarization Error Rate, senza finestra di tolleranza. Il "
                       "parlato non rilevato o rilevato a torto non è considerato.",
    "mass.vorbehalt": "Misura dell'intervento, non misura della precisione. Il tasso comprende ogni modifica a mano, anche "
                      "pseudonimizzazione, ripulitura del parlato e regole di trascrizione. Non coglie gli errori che "
                      "nessuno ha notato. Quantifica quanto si è intervenuti — non quanto siano buone la macchina "
                      "o la versione finale.",

    # ---- 2. Modulo metodologico ----
    "datei.methoden": "modulo-metodologico-trascrizione",
    "m.titel": "Modulo metodologico: trascrizione",
    "m.einleitung": "Una sezione metodologica descrive il corpus, non la singola intervista. Questo modulo riassume le "
                    "trascrizioni scelte: estensione, procedimento e in quale misura le trascrizioni automatiche "
                    "grezze sono state modificate a mano. Seguono un paragrafo da riprendere e "
                    "un elenco di ciò che sanno solo le ricercatrici e i ricercatori.",
    "m.korpus": "Corpus", "m.n": "Trascrizioni", "m.importiert": "di cui {n} importate, non trascritte nell'app",
    "m.gesamt": "Durata complessiva", "m.mittel": "Durata: media (intervallo)",
    "m.eigen": "tra cui un modello proprio del gruppo di ricerca, non compreso nell'elenco fornito con l'app",
    "m.diar": "in {n} trascrizioni su {gesamt} (SpeakerKit, pyannote community-1)",
    "m.zeitraum": "Periodo delle elaborazioni automatiche",
    "m.mass": "Misura dell'intervento sul corpus",
    "m.mass.text": "Calcolata per {n} trascrizioni su {gesamt} (per le altre non esiste uno stato iniziale).",
    "m.median": "Mediana (intervallo)",
    "m.absatz": "Paragrafo per la sezione metodologica",
    "m.absatz.hinweis": "Da riprendere e adattare. Le parentesi quadre vanno sostituite.",
    "m.absatz.text": "Le registrazioni (n = {n}; durata complessiva {gesamt}; media {mittel}, intervallo {spanne}) sono state "
                     "trascritte con ResearchTranscript {version} (B/IAS Basel, AGPL-3.0) interamente in locale [ su un "
                     "computer del gruppo di ricerca ]; l'app non trasmette nulla a servizi esterni. Il "
                     "riconoscimento vocale ha usato whisper.cpp {whisper} con il modello {modell} (Radford et al., 2022)."
                     "{diar} Le trascrizioni grezze sono state poi verificate [ da chi ] [ integralmente / a campione ] "
                     "a confronto con la registrazione, corrette secondo [ regole di trascrizione ] [ e pseudonimizzate "
                     "nel testo ]. Il tasso di correzione a livello di parola (calcolato come il tasso di errore "
                     "sulle parole, versione finale come riferimento, normalizzato) è stato in mediana pari a {norm}. "
                     "Il tasso misura l'intervento, pseudonimizzazione compresa, non la precisione.",
    "m.absatz.diar": " I parlanti sono stati separati con SpeakerKit e il modello pyannote community-1 (Plaquet & "
                     "Bredin, 2023); la quota di tempo di parola riassegnato a mano è stata in mediana pari a {sprechzeit}.",
    "m.offen": "Ciò che sanno solo le ricercatrici e i ricercatori",
    "m.offen.wer": "Chi ha corretto, con quale qualifica, e se il riascolto a confronto con la registrazione è stato integrale.",
    "m.offen.regeln": "Secondo quali regole di trascrizione si è lavorato (fedeltà letterale, ripulitura, pause, dialetto).",
    "m.offen.pseudonym": "Che cosa è stato pseudonimizzato e secondo quale regola; dove si trova la tabella di corrispondenza degli pseudonimi.",
    "m.offen.einwilligung": "Se il consenso delle persone intervistate copre il tipo di trattamento e una successiva trasmissione a terzi.",
    "m.je": "Per trascrizione",

    # ---- 3. Modulo per il registro ----
    "datei.verfahren": "modulo-registro-researchtranscript",
    "v.titel": "Modulo per il registro delle attività di trattamento, la valutazione d'impatto sulla protezione dei dati (DPIA) e la domanda alla commissione etica",
    "v.einleitung": "Questi documenti descrivono un'attività di trattamento o un progetto, non la singola "
                    "registrazione. Il modulo fornisce a tale scopo i fatti relativi all'app, così come è installata su "
                    "questo computer. Tutto ciò che sa soltanto il titolare del trattamento figura più sotto come campo "
                    "aperto. Il modulo non è una consulenza giuridica né una dichiarazione sulla liceità.",
    "v.schritte": "Che cosa fa l'app con una registrazione", "v.schritt": "Fase", "v.werkzeug": "Strumento",
    "v.wo": "Dove",
    "v.s1.a": "Lettura della traccia audio e conversione a 16 kHz mono", "v.s1.b": "macOS AVFoundation",
    "v.s1.c": "in locale, nel processo dell'app",
    "v.s2.a": "Rilevamento dell'attività vocale", "v.s2.b": "Silero VAD {silero} in whisper.cpp", "v.s2.c": "in locale",
    "v.s3.a": "Riconoscimento vocale: dall'audio al testo con marche temporali",
    "v.s3.b": "whisper.cpp {whisper} (programma ausiliario nel pacchetto dell'app), modello a scelta",
    "v.s3.c": "in locale, unità grafica (Metal)",
    "v.s4.a": "Separazione dei parlanti (disattivabile)", "v.s4.b": "SpeakerKit (Argmax) con pyannote community-1, Core ML",
    "v.s4.c": "in locale, Neural Engine",
    "v.s5.a": "Correzione nell'editor; cronologia e giornale per ogni trascrizione", "v.s5.b": "ResearchTranscript",
    "v.s5.c": "in locale",
    "v.s6.a": "Esportazione (VTT, CSV, TXT, Markdown, Word, REFI-QDA, dossier enrich; MP3 tramite LAME)",
    "v.s6.b": "ResearchTranscript", "v.s6.c": "in locale, nella cartella scelta dalla persona",
    "v.modelle": "Modelli di riconoscimento vocale attualmente disponibili su questo computer:", "v.herkunft": "Provenienza",
    "v.nicht": "Che cosa l'app non fa",
    "v.nicht.punkte": "Non stabilisce connessioni di rete: nessun account, nessuna telemetria, nessuna verifica di aggiornamenti, nessun rapporto di arresto anomalo proprio. I link (informativa sulla privacy, codice sorgente) si aprono nel browser solo con un clic.\n"
                      "Non scarica a posteriori né modelli né parti di programma.\n"
                      "Non gestisce alcun server né alcun servizio di rete; l'elaborazione avviene nel processo dell'app.\n"
                      "Funziona nella App Sandbox di macOS e legge soltanto le cartelle scelte dalla persona e i file che questa vi trascina.\n"
                      "Non contiene IA generativa: nulla viene riassunto, riformulato o interpretato.\n"
                      "Legge Zotero solo dopo un'attivazione esplicita e non lo modifica mai.",
    "v.ablage": "Dove si trovano i dati",
    "v.ablage.punkte": "Nella cartella della biblioteca scelta dalla persona; per ogni trascrizione una sottocartella con `transkript.json`, una copia della registrazione (per i video anche il file video) e `wellenform.json`.\n"
                       "`ausgang.json` conserva lo stato iniziale automatico inalterato, `history/` gli ultimi 30 stati precedenti a ogni salvataggio. Entrambi contengono il testo letterale PRIMA di una pseudonimizzazione.\n"
                       "Le trascrizioni eliminate restano nella cartella `_papierkorb` della biblioteca finché questa non viene svuotata nel Finder.\n"
                       "Le impostazioni e il registro dell'app si trovano nel contenitore dell'app dell'account utente; il registro può contenere nomi di file e messaggi di errore.\n"
                       "L'app non sa dove si trova la cartella della biblioteca né se viene salvata in un backup o sincronizzata.",
    "v.export": "Che cosa contengono le esportazioni",
    "v.export.punkte": "VTT, TXT: solo testo. CSV, Markdown, Word: testo e memo delle ricercatrici e dei ricercatori.\n"
                       "REFI-QDA (`.qdpx.zip`) e dossier enrich (`.enrich`): in più la registrazione audio, quindi la voce; con un video, su richiesta, anche il file video.\n"
                       "Dossier enrich: inoltre il giornale (con l'indirizzo e-mail, se indicato nelle impostazioni) e i metadati Zotero collegati.",
    "v.offen": "Da compilare a cura del titolare del trattamento",
    "v.offen.text": "L'app non può conoscere queste indicazioni. Senza di esse la voce è incompleta.",
    "v.eintrag": "Voce", "v.hinweis": "Nota",
    "v.offen.felder": "Titolare del trattamento :: istituzione, direzione del progetto, contatto\n"
                      "Consulenza per la protezione dei dati :: persona o servizio competente\n"
                      "Scopo del trattamento :: progetto di ricerca, domanda di ricerca\n"
                      "Base giuridica e diritto applicabile :: a seconda dell'ente, diritto cantonale, diritto federale o RGPD; l'app non lo sa\n"
                      "Persone interessate :: persone intervistate; terzi menzionati nel colloquio\n"
                      "Categorie di dati personali :: voce, dichiarazioni; eventualmente dati personali degni di particolare protezione\n"
                      "Destinatari :: chi riceve registrazioni, trascrizioni o esportazioni\n"
                      "Comunicazione all'estero :: nessuna da parte dell'app; possibile con la trasmissione di esportazioni o l'archiviazione nel cloud\n"
                      "Conservazione e cancellazione :: termini; anche per cestino, cronologia, stato iniziale e backup\n"
                      "Ubicazione della cartella della biblioteca :: disco interno, unità cifrata, unità di rete\n"
                      "Backup e sincronizzazione :: Time Machine, iCloud Drive, altri servizi — includono la cartella, se si trova lì\n"
                      "Protezione del dispositivo :: FileVault, blocco dello schermo, account utente separati\n"
                      "Persone autorizzate all'accesso :: chi può lavorare al computer e nella cartella\n"
                      "Informazione e consenso delle persone intervistate :: copre registrazione, trascrizione, conservazione, trasmissione a terzi?",
    "v.warnung": "A che cosa prestare attenzione",
    "v.warnung.punkte": "Pseudonimizzato non significa anonimizzato: i dati pseudonimizzati restano dati personali.\n"
                        "Viene pseudonimizzato il testo della versione finale. Registrazione, stato iniziale e cronologia continuano a contenere la voce e i nomi reali; chi non ne ha più bisogno li elimina nel Finder.\n"
                        "«In locale» è una proprietà dell'app, non del luogo di archiviazione: una cartella sincronizzata trasmette i dati.\n"
                        "I modelli propri del gruppo di ricerca non fanno parte dell'elenco fornito e documentato con l'app.",

    # ---- 4. Scheda per il deposito in un repository ----
    "datei.repositorium": "scheda-deposito-repository",
    "r.dok": "Scheda per il deposito in un repository",
    "r.einleitung": "Preparazione al deposito di {n} trascrizione/i come dati di ricerca con DOI. I campi seguono "
                    "DataCite 4 e il modulo di Zenodo, integrati con ciò che richiedono gli archivi specializzati in "
                    "dati qualitativi. Ciò che l'app conosce da Zotero e dalle trascrizioni è già inserito e "
                    "contrassegnato come proposta; tutto il resto è aperto. La scheda non sostituisce né la consulenza "
                    "dell'archivio né una consulenza giuridica.",
    "r.warnung": "Da leggere prima",
    "r.warnung.punkte": "La registrazione audio contiene la voce ed è un dato personale. Non viene pubblicata ad accesso aperto, nemmeno con uno pseudonimo.\n"
                        "Pseudonimizzato non significa anonimo; il diritto in materia di protezione dei dati continua ad applicarsi.\n"
                        "Nelle sue condizioni d'uso Zenodo esige che i dati personali sensibili, prima di una diffusione aperta, siano adeguatamente anonimizzati o coperti da un consenso, e per i dati sensibili non anonimizzati rimanda a piattaforme specializzate. La responsabilità è di chi carica i file.\n"
                        "I metadati (titolo, descrizione, parole chiave, nomi dei file) sono sempre pubblici, anche quando i file sono ad accesso chiuso. Non devono contenere dati personali.\n"
                        "Una voce DOI pubblicata non si può cancellare senza lasciare traccia.\n"
                        "Le persone intervistate non compaiono mai come autrici o autori. L'app propone da Zotero soltanto persone che non appartengono alla parte intervistata; ogni proposta va verificata.\n"
                        "La trascrizione è generata automaticamente e modificata a mano; lo stato delle correzioni va riportato nella documentazione (protocollo di trascrizione, modulo metodologico).",
    "r.status": "Stato", "r.erlaeuterung": "Spiegazione", "r.vorschlag": "proposta, da verificare",
    "r.st.pflicht": "obbligatorio", "r.st.empfohlen": "consigliato", "r.st.optional": "facoltativo",
    "r.st.archiv": "richiesto dagli archivi specializzati",
    "r.befragte_weg": "(Le persone della parte intervistata presenti in Zotero sono volutamente omesse.)",
    "r.g.beschreibung": "Descrizione", "r.g.personen": "Persone e ruoli", "r.g.rechte": "Diritti e accesso",
    "r.g.methode": "Contenuto e metodo", "r.g.dateien": "File", "r.g.ethik": "Etica e protezione dei dati",
    "r.titel": "Titolo del set di dati", "r.titel.e": "Descrittivo, senza nomi di persone intervistate.",
    "r.typ": "Tipo di risorsa", "r.typ.e": "Un pacchetto di trascrizioni e documentazione è considerato un Dataset.",
    "r.pubdatum": "Data di pubblicazione", "r.pubdatum.e": "Data della pubblicazione nel repository, non dell'intervista.",
    "r.abstract": "Descrizione", "r.abstract.e": "Di che cosa si tratta, chi è stato intervistato (in termini generali) e a quale scopo.",
    "r.schlagworte": "Parole chiave", "r.schlagworte.e": "Da tre a otto termini, possibilmente tratti da un vocabolario disciplinare.",
    "r.sprache": "Lingua/e", "r.sprache.e": "Lingua delle interviste come codice ISO.",
    "r.erhebung": "Periodo della raccolta dei dati", "r.erhebung.e": "Nel dubbio solo l'anno o il mese: una data precisa può rendere riconoscibili le persone.",
    "r.ort": "Luogo o regione", "r.ort.e": "Preciso solo quanto basta perché nessuno diventi riconoscibile.",
    "r.version": "Versione", "r.version.e": "Dopo le correzioni creare una nuova versione.",
    "r.publisher": "Repository", "r.publisher.e": "Nome del repository scelto (automatico su Zenodo).",
    "r.verwandt": "Pubblicazioni correlate", "r.verwandt.e": "DOI degli articoli che si basano sui dati.",
    "r.foerderung": "Finanziamento", "r.foerderung.e": "Ente finanziatore e numero del sussidio; FNS e DFG si aspettano l'indicazione.",
    "r.creators": "Autrici e autori (Creators)", "r.creators.e": "Le ricercatrici e i ricercatori responsabili del set di dati, con ORCID e istituzione. Mai le persone intervistate.",
    "r.contributors": "Collaboratrici e collaboratori con ruolo", "r.contributors.e": "p. es. DataCollector, ProjectLeader, Supervisor (ruoli secondo DataCite).",
    "r.kontakt": "Persona di contatto", "r.kontakt.e": "Chi risponderà alle richieste di accesso anche tra alcuni anni.",
    "r.rechteinhaber": "Titolare dei diritti", "r.rechteinhaber.e": "Di solito la scuola universitaria o le ricercatrici e i ricercatori.",
    "r.lizenz": "Licenza", "r.lizenz.e": "Obbligatoria per i file aperti, p. es. CC BY 4.0 per la documentazione; per i file sensibili un contratto d'uso al posto di una licenza aperta.",
    "r.zugang": "Livello di accesso per file", "r.zugang.e": "Aperto, limitato o chiuso — distintamente per documentazione, trascrizione e registrazione.",
    "r.embargo": "Embargo fino al", "r.embargo.e": "Differimento motivato, p. es. fino alla pubblicazione.",
    "r.bedingungen": "Condizioni per le richieste di accesso", "r.bedingungen.e": "Chi ottiene l'accesso e a quali condizioni.",
    "r.methode": "Metodo di raccolta dei dati", "r.methode.e": "p. es. intervista guidata da una traccia, in presenza o online.",
    "r.sampling": "Selezione delle persone intervistate", "r.sampling.e": "Popolazione di riferimento e modalità di selezione.",
    "r.umfang": "Estensione", "r.umfang.e": "Dati tecnici essenziali tratti dalle trascrizioni.",
    "r.umfang.wert": "{n} intervista/e, durata complessiva {dauer}",
    "r.technik": "Procedimento di trascrizione", "r.technik.e": "Generata automaticamente, modificata a mano; completare lo stato delle correzioni con i dati del modulo metodologico.",
    "r.technik.wert": "ResearchTranscript {version}, whisper.cpp {whisper}, modello {modell}; in locale",
    "r.konventionen": "Convenzioni di trascrizione", "r.konventionen.e": "Notazione per pause, sovrapposizioni, passaggi incomprensibili; completare qui ciò che va oltre il formato.",
    "r.konventionen.wert": "Marche temporali hh:mm:ss per ogni enunciato, parlante come indicazione separata; [ completare le regole ]",
    "r.anonymisierung": "Anonimizzazione", "r.anonymisierung.e": "Che cosa è stato sostituito e come; la tabella di corrispondenza degli pseudonimi non viene mai depositata.",
    "r.begleit": "Materiale di accompagnamento", "r.begleit.e": "Traccia d'intervista, foglio informativo, modello di consenso, rapporto metodologico, README.",
    "r.dateien.text": "File così come si trovano nella biblioteca, con somma di controllo (SHA-256). Per il deposito se ne "
                      "ricavano esportazioni; le somme di controllo delle esportazioni vanno calcolate dopo l'esportazione.",
    "r.formate": "Sui formati:",
    "r.formate.punkte": "Depositare le trascrizioni, oltre che in Word e REFI-QDA, anche in un formato di testo aperto (TXT, Markdown, CSV); gli archivi preferiscono formati semplici e aperti.\n"
                        "REFI-QDA è un formato di scambio con possibili perdite tra un programma e l'altro, non un formato di archiviazione da usare da solo.\n"
                        "L'MP3 nei pacchetti dell'app è una copia d'uso. Come master d'archivio gli archivi raccomandano FLAC o WAV — cioè la registrazione originale.\n"
                        "Ogni trascrizione ha bisogno di un'intestazione con identificativo, data e contesto; l'esportazione Markdown e Word dell'app la scrive.",
    "r.ethik.text": "Può rispondere soltanto il gruppo di ricerca. Finché un punto resta aperto, non si pubblica nulla.",
    "r.pruefpunkt": "Punto di verifica", "r.erledigt": "fatto",
    "r.ethik.punkte": "Il consenso copre l'archiviazione e il riutilizzo. :: Senza consenso documentato nessuna trasmissione a terzi.\n"
                      "Il consenso copre la trasmissione della registrazione audio. :: La voce è un dato personale.\n"
                      "Esiste un parere della commissione etica o una condizione da essa imposta. :: Indicare numero e organo.\n"
                      "Identificatori diretti e indiretti e terzi menzionati sono stati verificati. :: Attenzione a combinazioni come professione, luogo ed età.\n"
                      "Titolo, descrizione, parole chiave e nomi dei file sono privi di dati personali. :: I metadati sono sempre pubblici.\n"
                      "La tabella di corrispondenza degli pseudonimi è conservata separatamente. :: Non va mai depositata.\n"
                      "Stato iniziale e cronologia restano fuori. :: `ausgang.json` e `history/` contengono il testo letterale precedente alla pseudonimizzazione.\n"
                      "Il repository è adatto ai dati. :: Per i dati sensibili un archivio specializzato con controllo degli accessi.\n"
                      "Le direttive dell'ente finanziatore e della scuola universitaria sono state verificate. :: Motivare nel piano di gestione dei dati le eccezioni all'accesso aperto.",
    "r.wohin": "Quale repository", "r.repo": "Repository", "r.repo.fuer": "Idoneità",
    "r.repos": "Zenodo :: Generalista, DOI immediato; file ad accesso chiuso possibili, metadati sempre aperti. Per documentazione, strumenti e testi davvero anonimizzati; non per le registrazioni. :: https://zenodo.org\n"
               "SWISSUbase (FORS) :: Svizzera, scienze sociali; accetta dati qualitativi e sensibili con controllo degli accessi e contratto d'uso; DOI. :: https://www.swissubase.ch\n"
               "Qualiservice :: Germania, dati qualitativi; consulenza, aiuto per l'anonimizzazione, accesso solo su richiesta; DOI. :: https://www.qualiservice.org\n"
               "AUSSDA :: Austria, scienze sociali; direttiva propria per i dati qualitativi. :: https://aussda.at\n"
               "UK Data Service :: Regno Unito; accesso graduato (open, safeguarded, controlled). :: https://ukdataservice.ac.uk",
    "r.quellen": "Fonti",
    "r.quellen.punkte": "DataCite Metadata Schema 4: <https://schema.datacite.org>\n"
                        "Zenodo: campi <https://help.zenodo.org/docs/deposit/describe-records/>, linee guida <https://about.zenodo.org/policies/>, condizioni <https://about.zenodo.org/terms/>\n"
                        "CESSDA Data Management Expert Guide: <https://dmeg.cessda.eu>\n"
                        "FORS Guide n. 20, anonimizzazione di dati qualitativi: <https://doi.org/10.24449/FG-2023-00020>\n"
                        "FNS, Open Research Data: <https://www.snf.ch/de/FAiWVH4WvpKvohw9/thema/forschungsdaten>\n"
                        "DFG, gestione dei dati di ricerca: <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>\n"
                        "Modello di README della Cornell University (CC0): <https://data.research.cornell.edu/data-management/sharing/readme/>",
    # ---- Methodenbaustein für EIN Transkript (der Regelfall) ----
    'm.einleitung.eins': "Questo modulo descrive come è nata questa trascrizione e quanto la trascrizione grezza automatica è stata rivista a mano. Le affermazioni valgono per questo documento. Seguono un paragrafo da riprendere e l'elenco di ciò che solo il gruppo di ricerca sa.",
    'm.korpus.eins': 'Trascrizione',
    'm.mass.fehlt': "Per questa trascrizione non è più disponibile uno stato iniziale; la misura dell'intervento non può essere calcolata (vedi il protocollo di trascrizione).",
    'm.absatz.text.eins': "La registrazione (durata {gesamt}) è stata trascritta interamente in locale [ su un computer del gruppo di ricerca ] con ResearchTranscript {version} (B/IAS Basilea, AGPL-3.0); l'app non trasmette nulla a servizi esterni. Il riconoscimento vocale ha usato whisper.cpp {whisper} con il modello {modell} (Radford et al., 2022).{diar} La trascrizione grezza è stata poi verificata sulla registrazione [ da chi ] [ integralmente / a campione ], corretta secondo [ regole di trascrizione ] [ e pseudonimizzata nel testo ]. Il tasso di correzione a livello di parola (calcolato come il tasso di errore sulle parole, versione finale come riferimento, normalizzato) è stato di {norm}. Il tasso misura l'intervento, pseudonimizzazione compresa, non l'accuratezza.",
    'm.absatz.diar.eins': ' I parlanti sono stati separati con SpeakerKit e il modello pyannote community-1 (Plaquet & Bredin, 2023); il {sprechzeit} del tempo di parola è stato riassegnato a mano.',
}
