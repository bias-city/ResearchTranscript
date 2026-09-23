# ResearchTranscript — Scheda per ricercatrici e ricercatori

Che cos'è l'app, quale IA al suo interno fa che cosa, dove si trova il
codice e perché la trascrizione non lascia mai il computer. Da
consegnare alla direzione del progetto, al comitato etico o ai colleghi.
Stato al 23 settembre 2026, versione 0.6.2.

Questa scheda è il modello generale. Dalla versione 0.6.0 l'app genera
da sé la versione riferita alla singola trascrizione (Editor ›
Esporta › «Pacchetto di documentazione (.zip) …»): protocollo di
trascrizione con il modello e la versione effettivamente usati e la
misura rilevata della revisione manuale, paragrafo per la sezione
metodi, fatti per la protezione dei dati, scheda per il repository e
file di citazione.

## Che cosa fa l'app

ResearchTranscript trasforma registrazioni audio — interviste, discussioni
di gruppo, workshop — in testo con codici temporali e attribuzione dei
parlanti. La trascrizione viene poi corretta in un editor, i parlanti
vengono nominati, i nomi sostituiti, e il risultato esportato per
l'analisi (ATLAS.ti, MAXQDA, NVivo tramite REFI-QDA; enrich; WebVTT,
CSV, testo, Markdown, Word). Anche le registrazioni video (MP4/MOV) sono
accettate: il suono viene estratto, il video resta invariato con la
trascrizione e lascia il computer solo se lo si include esplicitamente
nell'export REFI-QDA. Tutto avviene sul proprio Mac.

## Quale IA fa che cosa

| Componente | Compito | Origine, licenza | Gira dove |
|---|---|---|---|
| whisper.cpp 1.8.2 con il modello `large-v3-turbo` | Riconoscimento vocale: audio → testo con codici temporali | modello di OpenAI (MIT), runtime whisper.cpp (MIT) | in locale, come programma ausiliario del pacchetto dell'app, sull'unità grafica del Mac (Metal) |
| Silero VAD 5.1.2 (in whisper.cpp) | Attività vocale: rileva dove si parla. Solo con la separazione dei parlanti disattivata; altrimenti è questa a tagliare i blocchi | MIT | in locale, nello stesso programma ausiliario |
| SpeakerKit (Argmax) con i modelli pyannote segmentation-3.0, WeSpeaker ResNet34 e pyannote community-1 | Separazione dei parlanti: riconosce i cambi di parlante, sovrapposizioni comprese, e raggruppa le voci; disattivabile | modelli da pyannote speaker-diarization-community-1 (CC BY 4.0), convertiti da Argmax in Core ML; motore SpeakerKit di Argmax (MIT) | in locale, nell'app, tramite Core ML |

Tutti i modelli sono contenuti nel pacchetto dell'app, che non scarica
né modelli né parti di programma (un altro modello whisper.cpp può
essere collocato a mano nella cartella «Modelle» della biblioteca; non
fa parte di questo elenco, e il giornale di ogni trascrizione indica il
modello usato). L'audio è letto da macOS stesso (AVFoundation), l'MP3 è
scritto da LAME (LGPL, collegato dinamicamente). Non c'è accesso a un
servizio di IA, nessun account, nessuna chiave.

**Nessun riassunto, nessuna riformulazione.** L'app non riassume e non
riformula nulla. I modelli non imparano dalle registrazioni.

**Limiti del riconoscimento vocale.** Il riconoscimento vocale è un
modello di IA. Dove non capisce nulla (rumori di fondo, dialetto,
sovrapposizioni) può inserire parole che non sono state dette. Una
trascrizione di ResearchTranscript è una **trascrizione grezza** che va
verificata a confronto con la registrazione; l'editor è fatto per
questo. Tedesco standard, francese, italiano e inglese vengono
riconosciuti bene, lo svizzero tedesco in modo lacunoso — i parlanti
vengono comunque separati correttamente.

## Dove si trova il codice

- Codice sorgente: <https://github.com/bias-city/ResearchTranscript>
- Licenza: AGPL-3.0-or-later, con un permesso aggiuntivo per la
  distribuzione tramite l'App Store — software libero, che può essere
  usato, esaminato, modificato e ridistribuito
- Sviluppato al B/IAS – Basel Institut für angewandte Stadtforschung,
  Beckenweg 6, 4056 Basilea, <https://bias.city>
- Pacchetto d'installazione (DMG): firmato e notarizzato con Apple
  Developer ID, pubblicato con le release su GitHub, con checksum
- Chi non si fida del binario: il repository contiene l'intera catena di
  build, l'app può essere compilata da sé

## La trascrizione non lascia il computer

- L'app non trasmette **registrazioni, testi o dati di utilizzo**:
  nessun account, nessuna telemetria, nessuna verifica di
  aggiornamenti, nessun rapporto di arresto anomalo proprio, nessun
  download di modelli. L'autorizzazione di rete di macOS è impostata
  solo perché la vista web integrata la richiede; un firewall o
  `nettop` mostra che non nasce alcuna connessione.
- Non esiste un servizio interno: nessun server, nessuna porta aperta.
  La logica dell'applicazione gira incorporata nell'app. Leggibile da
  chiunque: la shell `frontend/src-tauri/src/lib.rs` non avvia alcun
  server e non apre alcuna porta.
- L'app gira nell'App Sandbox di macOS: accesso solo alle cartelle
  scelte in una finestra di dialogo e ai file trascinati nell'app. Le
  autorizzazioni si trovano in `frontend/src-tauri/entitlements.plist`.
- Registrazione e trascrizione si trovano nella cartella della
  biblioteca scelta, una sottocartella per trascrizione:
  `transkript.json` (testo letterale, parlanti, memo, giornale, dati
  Zotero), una copia della registrazione, per i video anche il file
  video, `wellenform.json`, inoltre `ausgang.json` (lo stato così come
  lo ha fornito la macchina o un file importato) e `history/` (gli
  ultimi 30 stati). Ciò che viene eliminato resta nella cartella
  `_papierkorb` della biblioteca finché questa non viene svuotata nel
  Finder. Impostazioni e registro dell'app si trovano nel contenitore
  dell'app dell'account utente.
- Nessun servizio cloud, nessun account utente, nessun responsabile
  del trattamento, nessun trasferimento verso paesi terzi — perché
  nulla viene trasmesso.

Che cosa **non** è coperto: le copie di sicurezza del Mac (Time Machine,
iCloud Drive per la cartella Documenti) e i rapporti di arresto anomalo
di macOS stesso seguono le impostazioni di sistema, non l'app. Chi
colloca la cartella della biblioteca in una cartella sincronizzata
sincronizza le registrazioni.

## Pseudonimizzare i nomi

- **Rinominare i parlanti:** un nome nel pannello dei parlanti vale per
  tutti i segmenti di quella persona — « Parlante 1 » diventa « B3 » in
  un solo passaggio.
- **Nomi nel testo:** « Cerca e sostituisci » trova un nome in tutti i
  segmenti, mostra ogni occorrenza nel contesto e sostituisce una alla
  volta o tutte insieme — anche dove la trascrizione ha spezzato il nome
  a fine riga.
- **Che cosa l'app non decide:** quali informazioni sostituire — luoghi,
  datori di lavoro, eventi. Resta una decisione di chi fa ricerca.
- **La registrazione resta quella che è.** Viene pseudonimizzato il
  testo della versione finale. `ausgang.json` e `history/` contengono
  il testo letterale precedente a una pseudonimizzazione, la
  registrazione la voce e i nomi reali.
- **Che cosa contengono le esportazioni.** Tutti i formati di testo
  (VTT, CSV, TXT, Markdown, Word): testo letterale, nomi dei parlanti,
  marche temporali; CSV, Markdown e Word in più i memo; Markdown e Word,
  con un collegamento Zotero, un'intestazione con titolo, data, citekey
  e le persone di cui sono stati scelti i ruoli. REFI-QDA
  (`.qdpx.zip`): testo, memo e la registrazione audio, quindi la voce;
  su richiesta il file video. Dossier enrich (`.enrich`): testo,
  registrazione audio in MP3, giornale (identificativo
  dell'installazione, facoltativamente e-mail), dati Zotero; nessun
  memo. Chi vuole consegnare solo dati pseudonimizzati consegna un
  formato di testo e verifica memo e intestazione.

## Per la sezione metodi

> Le registrazioni sono state trascritte in locale con
> ResearchTranscript 0.6.2 (B/IAS Basilea, AGPL-3.0-or-later;
> riconoscimento vocale whisper.cpp con il modello large-v3-turbo,
> separazione dei parlanti con SpeakerKit e modelli pyannote) su un
> computer del gruppo di ricerca; l'app non trasmette dati. Le
> trascrizioni grezze sono poi state verificate a confronto con la
> registrazione, corrette e pseudonimizzate nel testo.

---

Fonte: <https://github.com/bias-city/ResearchTranscript> (cartella
`site/docs`). La scheda è pubblicata con licenza CC BY 4.0: uso e
adattamento liberi, anche commerciali, citando B/IAS e indicando le
modifiche.
