#!/usr/bin/env python3
"""Erzeugt appstore/ANLEITUNG.md und appstore/texte/<sprache>/*.txt.

EINE Quelle für alle App-Store-Texte (de/en/fr/it) — mit Längenprüfung
gegen Apples Grenzen (Name 30, Untertitel 30, Werbetext 170,
Schlagwörter 100, Beschreibung 4000, Neuerungen 4000, Review-Notizen
4000). Scheitert eine Grenze, bricht das Skript ab.

Aufruf: python3 scripts/appstore-anleitung.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUS = ROOT / "appstore"
VERSION = json.loads((ROOT / "frontend/package.json").read_text())["version"]

GRENZEN = {"name": 30, "untertitel": 30, "werbetext": 170, "schlagwoerter": 100,
           "beschreibung": 4000, "neu": 4000}
SPRACHEN = {"de": "Deutsch", "en": "Englisch (USA)", "fr": "Französisch", "it": "Italienisch"}

URLS = {
    "support": "https://bias.city/researchtranscript/",
    "marketing": "https://bias.city/researchtranscript/",
    "datenschutz": "https://bias.city/researchtranscript/privacy.html",
}
COPYRIGHT = "2026 B/IAS – Basel Institut für angewandte Stadtforschung"

T: dict[str, dict[str, str]] = {
    "de": {
        "name": "ResearchTranscript",
        "untertitel": "Transkribieren ohne Cloud",
        "werbetext": "Aufnahme rein, Transkript mit Sprechern raus — auf deinem Mac, ohne Cloud und ohne Konto. Für Interviews, Gruppengespräche und Feldaufnahmen in der Forschung.",
        "schlagwoerter": "Transkription,Interview,Sprecher,Diarisierung,qualitativ,Forschung,QDA,offline,Audio,Untertitel",
        "neu": "Erste Fassung im Mac App Store.",
        "beschreibung": """ResearchTranscript transkribiert Interviews, Gruppengespräche und Feldaufnahmen vollständig auf deinem Mac. Die Aufnahme verlässt den Rechner nie: keine Cloud, kein Konto, keine Netzverbindung.

TRANSKRIBIEREN
• Spracherkennung mit whisper.cpp, Modell large-v3-turbo mitgeliefert — Deutsch, Englisch, Französisch, Italienisch und viele weitere Sprachen
• Sprechertrennung auf der Neural Engine: Zahl der Sprechenden je Aufnahme vorgeben oder erkennen lassen
• Mehrere Dateien in die Warteliste ziehen, Sprecherzahl je Datei wählen, starten — die Liste übersteht einen Neustart
• Video (MP4, MOV mit H.264 oder HEVC) als Quelle: der Ton wird gelesen, das Bild läuft im Editor stumm mit
• Eigene whisper.cpp-Modelle, etwa ein Feintuning für Schweizerdeutsch, einfach in den Modelle-Ordner legen

KORRIGIEREN
• Editor mit Wellenform in den Farben der Sprechenden, zoombar, mit Abspielposition
• Ganz per Tastatur: Turn wechseln, abspielen und anhalten mitten im Tippen, Turn am Cursor teilen, mit dem vorigen verbinden
• Zwischenrufe an der Abspielposition einfügen — für Stellen, an denen durcheinander geredet wird
• Timecodes von Hand setzen, Sprechende umbenennen, umfärben, zusammenführen
• Suchen und Ersetzen über das ganze Transkript, Hörprobe je Stimme
• Jede Änderung wird gesichert; frühere Stände bleiben als Verlauf erhalten

WEITERGEBEN
• WebVTT, CSV und Text
• REFI-QDA (.qdpx) für ATLAS.ti, MAXQDA und NVivo — mit Audio, Zeitmarken und Sprechenden als Codes
• enrich-Dossier mit Änderungsjournal
• Auf Wunsch Metadaten aus der lokalen Zotero-Bibliothek: Titel, Datum, Interviewende, Citekey

DATENSCHUTZ
Die App erhebt keine Daten, hat keine Telemetrie und öffnet keine Netzverbindung. Alle Modelle sind enthalten, nichts wird nachgeladen. Für Verfahrensverzeichnis, Datenschutz-Folgenabschätzung, Ethikantrag und Methodenteil liegen fertige Textbausteine auf der Website.

FREIE SOFTWARE
ResearchTranscript ist Open Source unter der AGPL; der Quellcode liegt auf GitHub. Entwickelt am B/IAS – Basel Institut für angewandte Stadtforschung.

VORAUSSETZUNGEN
Mac mit Apple Silicon, macOS 14 oder neuer, rund 2 GB freier Speicher.""",
    },
    "en": {
        "name": "ResearchTranscript",
        "untertitel": "Transcribe interviews offline",
        "werbetext": "Recording in, speaker-labelled transcript out — on your Mac, with no cloud and no account. For interviews, group discussions and field recordings in research.",
        "schlagwoerter": "transcription,interview,speaker,diarization,qualitative,research,QDA,offline,audio,subtitles,speech",
        "neu": "First release on the Mac App Store.",
        "beschreibung": """ResearchTranscript transcribes interviews, group discussions and field recordings entirely on your Mac. The recording never leaves your computer: no cloud, no account, no network connection.

TRANSCRIBE
• Speech recognition with whisper.cpp, large-v3-turbo model included — English, German, French, Italian and many more languages
• Speaker separation on the Neural Engine: set the number of speakers per recording or let the app detect it
• Drop several files into the waiting list, choose the speaker count per file, start — the list survives a restart
• Video (MP4, MOV with H.264 or HEVC) as a source: the audio is read, the picture follows silently in the editor
• Your own whisper.cpp models, for example a Swiss German fine-tune, go straight into the model folder

CORRECT
• Editor with a zoomable waveform in the speakers' colours and a playhead
• Fully keyboard-driven: move between turns, play and pause while typing, split a turn at the cursor, merge with the previous one
• Insert interjections at the playhead — for passages where people talk over each other
• Set timecodes by hand; rename, recolour and merge speakers
• Find and replace across the whole transcript, voice sample per speaker
• Every change is saved; earlier states are kept as history

SHARE
• WebVTT, CSV and plain text
• REFI-QDA (.qdpx) for ATLAS.ti, MAXQDA and NVivo — with audio, timestamps and speakers as codes
• enrich dossier with a change journal
• Optional metadata from your local Zotero library: title, date, interviewers, citekey

PRIVACY
The app collects no data, has no telemetry and opens no network connection. All models are included; nothing is downloaded. Ready-made text for records of processing, data protection impact assessments, ethics applications and methods sections is available on the website.

FREE SOFTWARE
ResearchTranscript is open source under the AGPL; the source code is on GitHub. Developed at B/IAS – Basel Institut für angewandte Stadtforschung.

REQUIREMENTS
Mac with Apple silicon, macOS 14 or later, about 2 GB of free space.""",
    },
    "fr": {
        "name": "ResearchTranscript",
        "untertitel": "Transcription sans cloud",
        "werbetext": "Un enregistrement en entrée, une transcription avec locuteurs en sortie — sur ton Mac, sans cloud ni compte. Pour entretiens, groupes de discussion et terrains.",
        "schlagwoerter": "transcription,entretien,locuteur,diarisation,qualitatif,recherche,QDA,hors ligne,audio,sous-titres",
        "neu": "Première version sur le Mac App Store.",
        "beschreibung": """ResearchTranscript transcrit entretiens, discussions de groupe et enregistrements de terrain entièrement sur ton Mac. L’enregistrement ne quitte jamais l’ordinateur : pas de cloud, pas de compte, aucune connexion réseau.

TRANSCRIRE
• Reconnaissance vocale avec whisper.cpp, modèle large-v3-turbo inclus — français, allemand, anglais, italien et bien d’autres langues
• Séparation des locuteurs sur le Neural Engine : indique le nombre de personnes par enregistrement ou laisse l’application le détecter
• Glisse plusieurs fichiers dans la liste d’attente, choisis le nombre de locuteurs par fichier, lance — la liste survit à un redémarrage
• Vidéo (MP4, MOV en H.264 ou HEVC) comme source : le son est lu, l’image suit en silence dans l’éditeur
• Tes propres modèles whisper.cpp, par exemple un modèle affiné pour le suisse allemand, se déposent dans le dossier des modèles

CORRIGER
• Éditeur avec forme d’onde zoomable aux couleurs des locuteurs et tête de lecture
• Entièrement au clavier : passer d’un tour de parole à l’autre, lire et mettre en pause pendant la saisie, scinder un tour au curseur, fusionner avec le précédent
• Insérer des interventions à la position de lecture — pour les passages où l’on parle en même temps
• Régler les repères temporels à la main ; renommer, recolorer et fusionner les locuteurs
• Rechercher et remplacer dans toute la transcription, échantillon de voix par locuteur
• Chaque modification est enregistrée ; les états antérieurs restent disponibles dans l’historique

PARTAGER
• WebVTT, CSV et texte
• REFI-QDA (.qdpx) pour ATLAS.ti, MAXQDA et NVivo — avec audio, repères temporels et locuteurs comme codes
• Dossier enrich avec journal des modifications
• Sur demande, métadonnées de ta bibliothèque Zotero locale : titre, date, enquêteurs, clé de citation

CONFIDENTIALITÉ
L’application ne collecte aucune donnée, n’a aucune télémétrie et n’ouvre aucune connexion réseau. Tous les modèles sont inclus ; rien n’est téléchargé. Des textes prêts à l’emploi pour le registre des traitements, l’analyse d’impact, les demandes d’éthique et la partie méthodologique se trouvent sur le site web.

LOGICIEL LIBRE
ResearchTranscript est un logiciel libre sous licence AGPL ; le code source est sur GitHub. Développé au B/IAS – Basel Institut für angewandte Stadtforschung.

CONFIGURATION REQUISE
Mac avec puce Apple, macOS 14 ou ultérieur, environ 2 Go d’espace libre.""",
    },
    "it": {
        "name": "ResearchTranscript",
        "untertitel": "Trascrivere senza cloud",
        "werbetext": "Entra una registrazione, esce una trascrizione con i parlanti — sul tuo Mac, senza cloud né account. Per interviste, discussioni di gruppo e registrazioni sul campo.",
        "schlagwoerter": "trascrizione,intervista,parlante,diarizzazione,qualitativo,ricerca,QDA,offline,audio,sottotitoli",
        "neu": "Prima versione sul Mac App Store.",
        "beschreibung": """ResearchTranscript trascrive interviste, discussioni di gruppo e registrazioni sul campo interamente sul tuo Mac. La registrazione non lascia mai il computer: niente cloud, niente account, nessuna connessione di rete.

TRASCRIVERE
• Riconoscimento vocale con whisper.cpp, modello large-v3-turbo incluso — italiano, tedesco, inglese, francese e molte altre lingue
• Separazione dei parlanti sul Neural Engine: indica il numero di persone per registrazione o lascialo rilevare all’app
• Trascina più file nella lista d’attesa, scegli il numero di parlanti per file, avvia — la lista sopravvive a un riavvio
• Video (MP4, MOV in H.264 o HEVC) come sorgente: viene letto l’audio, l’immagine segue muta nell’editor
• I tuoi modelli whisper.cpp, per esempio un modello affinato per lo svizzero tedesco, vanno semplicemente nella cartella dei modelli

CORREGGERE
• Editor con forma d’onda zoomabile nei colori dei parlanti e indicatore di riproduzione
• Tutto da tastiera: passare da un turno all’altro, riprodurre e mettere in pausa mentre scrivi, dividere un turno al cursore, unirlo al precedente
• Inserire interventi alla posizione di riproduzione — per i passaggi in cui si parla uno sull’altro
• Impostare a mano i timecode; rinominare, ricolorare e unire i parlanti
• Cerca e sostituisci in tutta la trascrizione, campione vocale per parlante
• Ogni modifica viene salvata; gli stati precedenti restano nella cronologia

CONDIVIDERE
• WebVTT, CSV e testo
• REFI-QDA (.qdpx) per ATLAS.ti, MAXQDA e NVivo — con audio, marche temporali e parlanti come codici
• Dossier enrich con registro delle modifiche
• Su richiesta, metadati dalla tua biblioteca Zotero locale: titolo, data, intervistatori, citekey

PRIVACY
L’app non raccoglie dati, non ha telemetria e non apre connessioni di rete. Tutti i modelli sono inclusi; nulla viene scaricato. Sul sito trovi testi pronti per il registro dei trattamenti, la valutazione d’impatto, le richieste etiche e la sezione metodologica.

SOFTWARE LIBERO
ResearchTranscript è open source con licenza AGPL; il codice sorgente è su GitHub. Sviluppato al B/IAS – Basel Institut für angewandte Stadtforschung.

REQUISITI
Mac con chip Apple, macOS 14 o successivo, circa 2 GB di spazio libero.""",
    },
}

REVIEW_NOTIZEN = """ResearchTranscript works fully offline: no account, no login, no server, no telemetry. The network-client entitlement is present only because WebKit needs it to render the app's own bundled pages inside the sandbox; the app opens no network connections (verifiable with `nettop`).

Architecture: the UI is a WKWebView. The application logic is written in Python and runs inside the app process through an embedded CPython 3.13 interpreter linked as a framework — no socket, no interpreter child process. The interpreter executes only the scripts shipped in the bundle; the app never downloads code, models or other resources (Guideline 2.5.2). Audio decoding uses AVFoundation; MP3 encoding uses the bundled LAME library (LGPL, dynamically linked, source shipped with the app). Speaker diarisation (SpeakerKit, Core ML) runs in-process. Speech recognition uses one bundled helper, whisper-cli (whisper.cpp, Metal), launched by the app with the sandbox "inherit" entitlement; it reads a temporary WAV file inside the app container and the model file, and terminates with the job.

Files are accessed only through the Open/Save panels, drag and drop, or the library folder the user chooses on first launch (kept as a security-scoped bookmark). The optional e-mail field in the settings is written only into dossier files the user exports; it is never transmitted. The Zotero integration is optional, read-only, local, and requires the user to pick the Zotero folder.

How to test: the attached zip contains a 2-minute synthetic interview (two invented speakers, synthesised with macOS "say") and its reference text.
1. Launch the app and choose any folder as the library.
2. Drag housing-cooperatives-interview.mp3 into the "AI Transcript" tab, set "Speakers" to 2, click "Start transcription". It takes about 30 seconds on Apple silicon.
3. Click "Edit" on the finished run: the editor shows the transcript with two speakers, a waveform and playback.
4. "Export" writes WebVTT, CSV, text, REFI-QDA or an enrich dossier through the Save panel.

Requires Apple silicon and macOS 14 or later. Licence: AGPL-3.0-or-later with an additional permission for App Store distribution (LICENSE-EXCEPTION in the public repository, https://github.com/bias-city/ResearchTranscript). All third-party licences are listed inside the app (Settings → Licences → All licences)."""


def pruefe() -> None:
    fehler = []
    for sprache, texte in T.items():
        for feld, grenze in GRENZEN.items():
            n = len(texte[feld])
            if n > grenze:
                fehler.append(f"{sprache}.{feld}: {n} > {grenze}")
        if ", " in texte["schlagwoerter"]:
            fehler.append(f"{sprache}.schlagwoerter: Leerzeichen nach Komma verschwendet Zeichen")
    if len(REVIEW_NOTIZEN) > 4000:
        fehler.append(f"review: {len(REVIEW_NOTIZEN)} > 4000")
    if fehler:
        sys.exit("Grenzen verletzt:\n  " + "\n  ".join(fehler))


def block(text: str) -> str:
    return "```text\n" + text + "\n```"


def texte_abschnitt() -> str:
    z = []
    for sprache, titel in SPRACHEN.items():
        t = T[sprache]
        z += [f"### {titel} (`{sprache}`)", "",
              f"**Name** ({len(t['name'])}/30)", block(t["name"]), "",
              f"**Untertitel** ({len(t['untertitel'])}/30)", block(t["untertitel"]), "",
              f"**Werbetext** ({len(t['werbetext'])}/170) — lässt sich später ohne neue Version ändern", block(t["werbetext"]), "",
              f"**Schlagwörter** ({len(t['schlagwoerter'])}/100)", block(t["schlagwoerter"]), "",
              f"**Beschreibung** ({len(t['beschreibung'])}/4000)", block(t["beschreibung"]), "",
              f"**Neuerungen in dieser Version** ({len(t['neu'])}/4000)", block(t["neu"]), ""]
    return "\n".join(z)


def schreibe_dateien() -> None:
    for sprache, t in T.items():
        d = AUS / "texte" / sprache
        d.mkdir(parents=True, exist_ok=True)
        for feld, text in t.items():
            (d / f"{feld}.txt").write_text(text + "\n", encoding="utf-8")
    (AUS / "texte" / "review-notizen-en.txt").write_text(REVIEW_NOTIZEN + "\n", encoding="utf-8")


ANLEITUNG = """# ResearchTranscript in den Mac App Store — Schritt für Schritt

Stand {version} · erzeugt von `scripts/appstore-anleitung.py` (Texte dort
ändern, Skript neu laufen lassen — es prüft Apples Zeichengrenzen).

**Wer macht was.** Alles unter «Du» braucht deinen Apple-Account und
lässt sich nicht automatisieren. Alles unter «Claude» ist vorbereitet
oder läuft per Skript. Die Bezeichnungen in Apples Portalen ändern sich
gelegentlich; gemeint ist immer der sinngemäss gleiche Punkt.

| | Du | Claude |
|---|---|---|
| Zertifikate, Profil, App-Eintrag, Texte einfügen, Screenshots hochladen, einreichen | ✔ | |
| Build signieren, paketieren, prüfen, hochladen (`scripts/release-mas.mjs`) | | ✔ |
| Datenschutzseite und LAME-Quelle auf bias.city legen | | ✔ (auf dein Go) |
| Texte (4 Sprachen), Screenshots (hell/dunkel), Review-Notizen, Demo-Zip | | ✔ liegt bereit |

**Was bereitliegt**

```
appstore/
  ANLEITUNG.md                      diese Datei
  texte/<de|en|fr|it>/*.txt         jeder Text einzeln, zum Kopieren
  texte/review-notizen-en.txt       Review-Notizen (Englisch)
  screenshots/<sprache>/<hell|dunkel>/<BxH>/01…07-*.png
docs/demo/researchtranscript-demo.zip   Anhang für die Review
site/privacy.html                   Datenschutzerklärung (4 Sprachen)
LICENSE-EXCEPTION                   AGPL-§7-Zusatzerlaubnis für den Store
```

---

## Teil A — Einmalig: Apple Developer (developer.apple.com/account)

### A1. Zertifikatsanfrage (CSR) am Mac erzeugen — 2 min

1. **Schlüsselbundverwaltung** öffnen → Menü *Schlüsselbundverwaltung →
   Zertifikatsassistent → Zertifikat einer Zertifizierungsinstanz
   anfordern …*
2. E-Mail: deine Apple-ID-Adresse · Name: `ben pohl` · *Auf der
   Festplatte sichern* · Fortfahren → `CertificateSigningRequest.certSigningRequest`
   auf den Schreibtisch.
3. Dieselbe Datei reicht für beide Zertifikate unten. Der private
   Schlüssel bleibt in deinem Schlüsselbund «Anmeldung» — die Zertifikate
   funktionieren nur auf diesem Mac (oder nach Export als .p12).

### A2. App-ID anlegen — 3 min

*Certificates, Identifiers & Profiles → Identifiers → +*

1. **App IDs** → Continue → Typ **App** → Continue.
2. Description: `ResearchTranscript` · Bundle ID: **Explicit** →
   `city.bias.researchtranscript`
3. Capabilities: **nichts ankreuzen** (die App Sandbox ist ein
   Entitlement im Build, keine Portal-Capability).
4. Continue → Register.

### A3. Zwei Zertifikate — 5 min

*Certificates → +*, zweimal:

| Auswahl im Portal | Wofür | So heisst es danach im Schlüsselbund |
|---|---|---|
| **Apple Distribution** | signiert die App | `Apple Distribution: ben pohl (CCRJ4A42D3)` |
| **Mac Installer Distribution** | signiert das .pkg | `3rd Party Mac Developer Installer: ben pohl (CCRJ4A42D3)` |

Jeweils: CSR aus A1 hochladen → Download → die `.cer`-Datei
doppelklicken (landet im Schlüsselbund «Anmeldung»).

Prüfen im Terminal:

```sh
security find-identity -v | grep -E "Apple Distribution|Mac Developer Installer"
```

Beide Zeilen müssen erscheinen.

### A4. Provisioning-Profil — 3 min

*Profiles → +*

1. Unter **Distribution**: **Mac App Store Connect** (früher «Mac App
   Store») → Continue.
2. Profiltyp **Mac** (nicht Mac Catalyst) · App ID:
   `city.bias.researchtranscript` → Continue.
3. Zertifikat: das **Apple Distribution** aus A3 → Continue.
4. Name: `ResearchTranscript MAS` → Generate → Download.
5. Datei umbenennen und ablegen unter:

```
~/Claude/enrich-transcript-spike/frontend/src-tauri/profiles/ResearchTranscript.provisionprofile
```

(Der Ordner `profiles/` ist in `.gitignore` — das Profil kommt nie ins Repo.)

---

## Teil B — Einmalig: App Store Connect (appstoreconnect.apple.com)

### B1. Verträge und Händlerstatus — 5 min

1. **Business** (früher «Verträge, Steuern, Bankdaten»): der Vertrag
   **Free Apps** muss aktiv sein. Für eine kostenlose App braucht es
   keine Bank- oder Steuerdaten.
2. **EU-Händlerstatus (Digital Services Act):** unter *Business →
   Compliance* angeben, ob du als **Händler (trader)** auftrittst.
   Ohne diese Angabe wird die App in der EU nicht ausgeliefert.
   Als Institut, das Software im Rahmen seiner Tätigkeit anbietet, ist
   «Händler» die naheliegende Angabe — dann erscheinen Adresse, Telefon
   und E-Mail des B/IAS auf der EU-Produktseite. *Das ist eine rechtliche
   Selbsteinschätzung; im Zweifel kurz klären.*

### B2. API-Schlüssel für den Upload — 3 min (empfohlen)

*Users and Access → Integrations → App Store Connect API → Team Keys → +*

1. Name `ResearchTranscript Upload` · Zugriff **App Manager** → Generate.
2. **Download API Key** (geht nur einmal) → `AuthKey_XXXXXXXXXX.p8`.
3. Ablegen und merken:

```sh
mkdir -p ~/.appstoreconnect/private_keys
mv ~/Downloads/AuthKey_*.p8 ~/.appstoreconnect/private_keys/
```

4. **Key ID** (10 Zeichen) und **Issuer ID** (UUID, oben auf der Seite)
   an Claude geben — nur diese beiden Werte, nicht die .p8-Datei.

Ohne API-Schlüssel geht der Upload auch von Hand mit der App
**Transporter** (Mac App Store): das `.pkg` hineinziehen → Deliver.

### B3. App anlegen — 3 min

*Apps → + → New App*

| Feld | Wert |
|---|---|
| Platforms | **macOS** |
| Name | `ResearchTranscript` |
| Primary Language | **English (U.S.)** — die Primärsprache sieht, wer keine der vier Sprachen eingestellt hat |
| Bundle ID | `city.bias.researchtranscript` (aus A2) |
| SKU | `researchtranscript-mac` |
| User Access | Full Access |

Danach unter der Versionsseite rechts bei den Sprachen **German, French,
Italian** hinzufügen (*Add Localization* / Sprachmenü oben rechts).

---

## Teil C — Seiten der App ausfüllen

### C1. App Information

| Feld | Wert |
|---|---|
| Subtitle | je Sprache, siehe Teil F |
| Category | Primary **Productivity** · Secondary **Education** |
| Content Rights | «Does not contain, show, or access third-party content» (Modelle und Bibliotheken sind Programmbestandteile, kein Inhalt Dritter) |
| Age Rating | Fragebogen überall **None / No** → ergibt **4+** |
| License Agreement | Apples Standard-EULA belassen |

### C2. Pricing and Availability

Price **0 (Free)** · Availability **All countries or regions** · keine
Vorbestellung · «Make this app available on Apple silicon Macs»
betrifft iOS-Apps — hier nichts zu tun.

### C3. App Privacy

1. **Privacy Policy URL:** `{datenschutz}`
2. *Get Started* → «Do you or your third-party partners collect data
   from this app?» → **No, we do not collect data from this app** →
   Publish. Ergebnis auf der Produktseite: «Data Not Collected».

### C4. Versionsseite «macOS App {version}»

Je Sprache (Sprachmenü oben rechts umschalten):

| Feld | Quelle |
|---|---|
| Screenshots | `appstore/screenshots/<sprache>/…` — siehe Teil E |
| Promotional Text | `texte/<sprache>/werbetext.txt` |
| Description | `texte/<sprache>/beschreibung.txt` |
| Keywords | `texte/<sprache>/schlagwoerter.txt` |
| Support URL | `{support}` |
| Marketing URL | `{marketing}` |
| What's New | erst ab der zweiten Version sichtbar; `texte/<sprache>/neu.txt` |

Einmal für alle Sprachen:

| Feld | Wert |
|---|---|
| Copyright | `{copyright}` |
| Version | `{version}` (muss zur Version im Build passen) |
| Build | nach Teil D auswählen |

### C5. App Review Information

| Feld | Wert |
|---|---|
| Sign-in required | **Nein** (Haken entfernen) |
| Contact | dein Name, Telefon, E-Mail |
| Notes | `texte/review-notizen-en.txt` (Englisch, {review_n}/4000 Zeichen) |
| Attachment | `docs/demo/researchtranscript-demo.zip` |

### C6. Version Release

**Manually release this version** — dann bestimmst du den Tag der
Veröffentlichung selbst (Website, Release-Notes).

---

## Teil D — Build hochladen (Claude, wenn A und B stehen)

Sag Bescheid, sobald Zertifikate und Profil liegen (A3, A4) und du Key ID
und Issuer ID hast (B2). Dann läuft:

```sh
cd ~/Claude/enrich-transcript-spike
APPLE_API_KEY_ID=XXXXXXXXXX APPLE_API_ISSUER=xxxxxxxx-xxxx-… \\
  node scripts/release-mas.mjs --upload
```

Das Skript baut die App mit Store-Entitlements, signiert mit «Apple
Distribution», bettet das Profil ein, prüft Signatur, Sandbox,
`inherit` des Whisper-Helfers und fremde Bibliothekspfade, baut das
`.pkg` mit dem Installer-Zertifikat, validiert bei Apple und lädt hoch.

Danach (10–30 min Verarbeitung bei Apple, E-Mail «build has completed
processing»):

1. **TestFlight → macOS → Builds:** der Build erscheint. Bei «Missing
   Compliance» → *Manage* → «None of the algorithms mentioned above»
   (die Info.plist sagt bereits `ITSAppUsesNonExemptEncryption = false`;
   meist entfällt die Frage).
2. **Internal Testing:** Gruppe anlegen, dich selbst hinzufügen, den
   Build in der App **TestFlight** am Mac installieren und einmal ganz
   durchspielen: Erststart (Ordnerdialog) → Datei hineinziehen →
   transkribieren → im Editor abspielen → Export auf den Schreibtisch →
   Einstellungen: Zotero-Ordner wählen → App beenden, neu starten
   (Bibliothek ohne neuen Dialog erreichbar = Bookmarks funktionieren).
3. Wenn das sitzt: auf der Versionsseite (C4) unter **Build** den Build
   wählen.

---

## Teil E — Screenshots

Apple verlangt für den Mac **eine** der Grössen 1280×800, 1440×900,
2560×1600 oder 2880×1800 (16:10), 1 bis 10 Bilder je Sprache. Es genügt,
**2880×1800** hochzuladen; Apple skaliert herunter. Die anderen Grössen
liegen bereit, falls du sie lieber einzeln pflegst.

```
appstore/screenshots/
  de/ en/ fr/ it/
    hell/ dunkel/
      1280x800/ 1440x900/ 2560x1600/ 2880x1800/
        01-editor.png             Transkript, Sprecher, Wellenform
        02-ai-transkript.png      Warteliste mit Sprecherzahl je Datei
        03-bibliothek.png         Bibliothek
        04-suchen-ersetzen.png    Suchen und Ersetzen
        05-sprecherfarbe.png      Farbe je Sprecher:in wählen
        06-export.png             Exportformate
        07-einstellungen.png      Einstellungen, Datenschutz, Lizenzen
```

**Vorschlag für die Reihenfolge** (die ersten drei sieht man ohne
Blättern): `hell/01-editor`, `hell/02-ai-transkript`, `dunkel/01-editor`,
`hell/06-export`, `hell/04-suchen-ersetzen`, `hell/05-sprecherfarbe`,
`hell/03-bibliothek`, `dunkel/02-ai-transkript`, `hell/07-einstellungen`.

Hochladen: auf der Versionsseite je Sprache die Bilder in das Feld
ziehen; Reihenfolge per Ziehen ändern. Gezeigt wird das erfundene
Interview aus `docs/demo` (zwei synthetische Stimmen) — kein echtes
Forschungsmaterial.

Neu aufnehmen (z. B. nach einer Oberflächenänderung):

```sh
cd ~/Claude/enrich-transcript-spike
(cd frontend && npm run build) && node scripts/appstore-screenshots.mjs
```

---

## Teil F — Texte (vier Sprachen)

Schlagwörter enthalten bewusst **keine fremden Marken** (ATLAS.ti,
MAXQDA, NVivo, Whisper): Apple lehnt Marken Dritter im Schlagwortfeld
ab. In der Beschreibung dürfen sie stehen — dort beschreiben sie die
Kompatibilität. Der App-Name wird ohnehin durchsucht und braucht kein
Schlagwort.

{texte}

### Review-Notizen (Englisch, {review_n}/4000)

{review}

---

## Teil G — Einreichen

1. Versionsseite: alle Pflichtfelder grün, Build gewählt, Screenshots in
   allen vier Sprachen.
2. **Add for Review** → **Submit to App Review**.
3. Übliche Dauer 1–3 Tage. Rückfragen kommen per E-Mail und im
   **Resolution Center**; die wahrscheinlichsten und die Antworten:

| Rückfrage | Antwort |
|---|---|
| Wozu das Netzwerk-Entitlement, wenn die App offline ist? | WKWebView lädt in der Sandbox ohne `network.client` auch lokale Seiten nicht; die App öffnet keine Verbindung (Review-Notizen, Absatz 1). |
| Lädt oder führt die App Code nach (2.5.2)? | Nein: der eingebettete Interpreter führt nur gebündelte Skripte aus, Modelle sind im Bundle; eigene Modelle legt die Person selbst in einen Ordner — Daten, kein Code. |
| Hilfsprogramm im Bundle? | `whisper-cli`, sandboxed mit `inherit`, liest nur eine temporäre Datei im Container. |
| Lizenz (AGPL) und Store-Bedingungen? | Zusatzerlaubnis nach AGPL §7 in `LICENSE-EXCEPTION`; alleiniger Rechteinhaber. |

4. Nach «Ready for Distribution»: **Release This Version**.

## Teil H — Danach

- Website: Knopf «Im Mac App Store laden» (Apples Badge:
  developer.apple.com/app-store/marketing/guidelines) neben dem
  DMG-Download.
- Jede neue Version: Build hochladen (Teil D), «What's New» je Sprache,
  einreichen. Werbetext lässt sich jederzeit ohne Review ändern.
- Das DMG auf GitHub bleibt der zweite Kanal (gleicher Code, gleiche
  Sandbox, Developer-ID-Signatur).
"""


def main() -> None:
    pruefe()
    schreibe_dateien()
    md = ANLEITUNG.format(version=VERSION, texte=texte_abschnitt(), review=block(REVIEW_NOTIZEN),
                          review_n=len(REVIEW_NOTIZEN), copyright=COPYRIGHT, **URLS)
    (AUS / "ANLEITUNG.md").write_text(md, encoding="utf-8")
    for sprache, t in T.items():
        print(sprache, {f: f"{len(t[f])}/{g}" for f, g in GRENZEN.items()})
    print(f"Review-Notizen {len(REVIEW_NOTIZEN)}/4000 · {AUS / 'ANLEITUNG.md'}")


if __name__ == "__main__":
    main()
