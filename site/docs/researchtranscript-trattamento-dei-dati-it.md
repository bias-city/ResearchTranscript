# ResearchTranscript — Descrizione del trattamento dei dati

Blocco di testo da inserire in un registro delle attività di
trattamento, una valutazione d'impatto sulla protezione dei dati, una
domanda al comitato etico o un piano di gestione dei dati. Stato al
18 settembre 2026, ResearchTranscript 0.6.0. Le voci tra `[parentesi
quadre]` vengono completate dal titolare del trattamento.

Il testo descrive che cosa il software fa e che cosa non fa. La
qualificazione giuridica del proprio trattamento — secondo il GDPR o la
nLPD svizzera — spetta al titolare; il testo non sostituisce una
consulenza legale.

Questo testo è il modello generale. Dalla versione 0.6.0 l'app genera
da sé la versione riferita alla singola trascrizione (Editor ›
Esporta › «Pacchetto di documentazione (.zip) …»): protocollo di
trascrizione con il modello e la versione effettivamente usati e la
misura rilevata della revisione manuale, paragrafo per la sezione
metodi, fatti per la protezione dei dati, scheda per il repository e
file di citazione.

---

## 1. Software impiegato

ResearchTranscript, versione `[0.6.0]`. Software libero sotto
AGPL-3.0-or-later (con un permesso aggiuntivo per la distribuzione
tramite l'App Store), sviluppato al B/IAS – Basel Institut für
angewandte Stadtforschung. Codice sorgente pubblico:
<https://github.com/bias-city/ResearchTranscript>; il pacchetto
d'installazione (DMG), firmato e notarizzato, è pubblicato lì con le
release. Il software gira come applicazione locale su macOS (Apple
Silicon), nell'App Sandbox di macOS, ed è installato e gestito dal
titolare stesso.

## 2. Finalità del trattamento

Conversione di registrazioni audio `[p. es. interviste semi-strutturate
nel progetto …]` in testo con codici temporali e attribuzione dei
parlanti, ai fini della successiva analisi qualitativa `[in ATLAS.ti /
MAXQDA / NVivo / enrich / …]`.

## 3. Interessati e categorie di dati

Gli interessati sono le persone registrate `[intervistati, partecipanti
a discussioni di gruppo, …]`. Vengono trattate registrazioni vocali
(voce e contenuto della conversazione) e le trascrizioni da esse
prodotte, con codici temporali e attribuzione dei parlanti. A seconda
del contenuto possono essere coinvolte categorie particolari di dati
personali `[sì / no: …]`.

## 4. Flusso dei dati di una trascrizione

1. **Ingresso.** Il file audio o video viene letto dal file system
   locale del dispositivo (audio: MP3, WAV, M4A, OGG, FLAC; video: MP4,
   MOV, M4V in H.264/HEVC — da un video viene letta solo la traccia
   audio, il video non viene mai convertito). L'audio è letto da macOS
   AVFoundation. L'App Sandbox di macOS consente l'accesso solo alle
   cartelle che la persona sceglie in una finestra di dialogo e ai file
   trascinati nell'app.
2. **Elaborazione.** La logica dell'applicazione gira incorporata
   nell'app. Il riconoscimento vocale (whisper.cpp 1.8.2, modello
   large-v3-turbo) gira come programma ausiliario del pacchetto
   dell'app, sull'unità grafica (Metal). La separazione dei parlanti
   (SpeakerKit di Argmax con i modelli pyannote segmentation-3.0,
   WeSpeaker ResNet34 e pyannote community-1, convertiti da Argmax in
   Core ML) gira nell'app tramite Core ML ed è disattivabile. Il
   rilevamento dell'attività vocale (Silero VAD 5.1.2 in whisper.cpp)
   viene usato solo se la separazione dei parlanti è disattivata;
   altrimenti i blocchi sono tagliati dalla separazione dei parlanti.
   Tutti i modelli sono contenuti nel pacchetto dell'applicazione, che
   non scarica né modelli né parti di programma. Altri modelli
   whisper.cpp si possono aggiungere solo a mano, nella cartella
   «Modelle» della biblioteca. I modelli non imparano dalle
   registrazioni. L'applicazione non riassume e non riformula nulla; il
   riconoscimento vocale è un modello di IA e può inserire parole che
   non sono state dette, perciò la trascrizione va verificata a
   confronto con la registrazione.
3. **Archiviazione.** Per ogni trascrizione viene creata una
   sottocartella nella cartella della biblioteca scelta `[percorso]`
   con `transkript.json` (testo letterale, parlanti, memo, giornale,
   dati Zotero), una copia della registrazione (per i video anche il
   file video invariato) e `wellenform.json`. `ausgang.json` conserva
   lo stato così come lo ha fornito la macchina o un file importato;
   `history/` conserva gli ultimi 30 stati. **Entrambi contengono il
   testo letterale precedente a una pseudonimizzazione.** Impostazioni
   e registro dell'app si trovano nel contenitore dell'app dell'account
   utente. Il giornale annota un identificativo dell'installazione e,
   facoltativamente, un indirizzo e-mail di chi rivede il testo.
4. **Rete.** Il software non trasmette registrazioni, testi o dati di
   utilizzo: nessun account, nessuna telemetria, nessuna verifica di
   aggiornamenti, nessun rapporto di arresto anomalo proprio, nessun
   download di modelli. Non esistono un servizio interno, un server o
   una porta aperta. L'autorizzazione di rete di macOS è impostata solo
   perché la vista web integrata la richiede; un firewall o `nettop`
   mostra che non nasce alcuna connessione. I rapporti di arresto
   anomalo del sistema macOS sono regolati dalle sue impostazioni di
   sistema, non dal software.
5. **Uscita.** I file di esportazione vengono scritti dove chi opera li
   salva. Tutti i formati di testo (VTT, CSV, TXT, Markdown, Word)
   contengono testo letterale, nomi dei parlanti e marche temporali;
   CSV, Markdown e Word in più i memo; Markdown e Word, con un
   collegamento Zotero, un'intestazione con titolo, data, citekey e le
   persone di cui sono stati scelti i ruoli. **REFI-QDA (`.qdpx.zip`)
   contiene testo, memo e la registrazione audio, quindi la voce, e su
   richiesta il file video; il dossier enrich (`.enrich`) contiene
   testo, registrazione audio in MP3 (tramite LAME), giornale con
   identificativo dell'installazione ed e-mail e dati Zotero, nessun
   memo.** Consegnarli significa consegnare la registrazione. Con il
   consenso Zotero l'applicazione legge il database locale
   `zotero.sqlite` in sola lettura, solo su richiesta. Per una
   registrazione video il file video è conservato invariato nella
   cartella della trascrizione (i volti sono dati personali, biometrici
   se identificabili).

## 5. Luogo del trattamento

Esclusivamente sul dispositivo `[dispositivo, luogo]`, nella sessione
della persona che ha effettuato l'accesso. Non esistono server, porte
aperte, servizi cloud né account utente.

## 6. Destinatari, responsabili del trattamento, trasferimenti verso paesi terzi

Nessuno. Poiché nessun dato viene trasmesso, non vi sono destinatari,
responsabili del trattamento né trasferimenti verso paesi terzi. I dati
lasciano il dispositivo solo se il titolare stesso consegna file di
esportazione `[a …, tramite …]`.

## 7. Conservazione e cancellazione

Conservazione di registrazioni e trascrizioni: `[durata, base]`.
Eliminare nell'applicazione sposta una voce in una cartella cestino
all'interno della biblioteca (`_papierkorb`); viene rimossa
definitivamente solo svuotando quella cartella nel Finder `[da chi,
quando]`. `ausgang.json` e gli stati in `history/` si trovano nella
cartella della rispettiva trascrizione e vengono cancellati con essa.
Le copie di sicurezza del dispositivo `[Time Machine, …]` seguono la
regola di cancellazione del titolare.

## 8. Misure tecniche e organizzative

A carico del titolare, poiché il software non porta con sé alcun
controllo degli accessi:

- Cifratura del disco, p. es. FileVault: `[attiva dal …]`
- Protezione dell'accesso al dispositivo (login, blocco schermo): `[…]`
- Pseudonimizzazione prima di ogni consegna — nell'editor
  dell'applicazione i parlanti possono essere rinominati e i nomi nel
  testo sostituiti con cerca-e-sostituisci; la decisione su che cosa
  sostituire spetta a chi corregge: `[procedura, responsabilità]`
- Regola per le copie di sicurezza: `[…]`
- Regola per la consegna dei file di esportazione, in particolare di
  quelli con audio: `[…]`

## 9. Base giuridica e informazione degli interessati

`[consenso / interesse legittimo / privilegio di ricerca ai sensi di …;
lettera informativa del …]`. Il software non contribuisce in alcun modo.

## 10. Verificabilità

Le affermazioni della sezione 4 sono verificabili nel codice sorgente:
la shell `frontend/src-tauri/src/lib.rs` non avvia alcun server e non
apre alcuna porta; le autorizzazioni della sandbox si trovano in
`frontend/src-tauri/entitlements.plist`. Il repository contiene
l'intera catena di build fino al pacchetto d'installazione firmato; chi
non si fida del binario distribuito può compilarlo.

---

Fonte di questo testo: <https://github.com/bias-city/ResearchTranscript>
(cartella `site/docs`). È pubblicato con licenza CC BY 4.0: uso e
adattamento liberi, anche commerciali, citando B/IAS e indicando le
modifiche.
