"""Textes du paquet de documentation — français. Clés, paramètres et structure des listes identiques à de.py."""

T = {
    # ---- général ----
    "feld": "Champ", "wert": "Valeur", "datei": "Fichier", "groesse": "Taille", "hinweis": "Remarque",
    "eintrag": "Entrée", "dezimal": ",", "nicht_aufgezeichnet": "non consigné",
    "fuss": "Généré par ResearchTranscript {v} le {datum} pour « {name} ». Les chercheuses et chercheurs remplissent les champs ouverts `[ … ]`.",
    "von": "{n} sur {gesamt} ({anteil})",

    # ---- dossiers et noms de fichiers (ASCII, minuscules, traits d'union) ----
    "paket.ordner": "documentation", "ordner.methoden": "1-methodes", "ordner.datenschutz": "2-protection-des-donnees",
    "ordner.ablage": "3-depot-des-donnees", "ordner.zitieren": "citer",
    "datei.liesmich": "LISEZMOI", "datei.protokoll": "protocole-de-transcription",
    "datei.absatz": "paragraphe-methodes", "datei.tatsachen": "faits-sur-l-app",
    "datei.stelle": "indications-du-responsable", "datei.datensatz": "fiche-jeu-de-donnees",
    "datei.interview": "fiche-entretien", "datei.ethik": "liste-ethique",
    "datei.repos": "entrepots-et-exigences",

    # ---- LISEZMOI ----
    "l.titel": "Paquet de documentation",
    "l.text": "Documents d'accompagnement d'une transcription, générés à partir des valeurs que l'application connaît. Le paquet ne contient ni transcription ni enregistrement.",
    "l.wofuer": "Usage",
    "l.zeilen": "{methoden}/{protokoll} :: Comment la transcription a été produite et dans quelle mesure elle a été révisée à la main. Fait partie de la documentation des données.\n"
                "{methoden}/{absatz} :: Paragraphe pour la partie méthodes, en version courte et en version détaillée.\n"
                "{datenschutz}/{tatsachen} :: Ce que l'application fait et ne fait pas. Pour le registre des activités de traitement, l'analyse d'impact relative à la protection des données, la demande d'éthique.\n"
                "{datenschutz}/{stelle} :: Ce que seul le responsable du traitement sait, sous forme de formulaire.\n"
                "{ablage}/{datensatz} :: Champs pour Zenodo et DataCite, une fois par jeu de données.\n"
                "{ablage}/{interview} :: Indications sur cet entretien précis.\n"
                "{ablage}/{ethik} :: Points de contrôle avant une publication.\n"
                "{ablage}/{repos} :: Quel entrepôt, quels formats, quelles exigences.\n"
                "{zitieren}/researchtranscript.bib :: Logiciel et modèles comme entrées pour Zotero (Fichier › Importer).",
    "l.vorher": "Avant la transmission",
    "l.vorher.punkte": "Le nom de la transcription, le fichier source et les noms de fichiers de ce paquet peuvent nommer des personnes. À vérifier avant la transmission.\n"
                       "L'enregistrement audio contient la voix et constitue une donnée personnelle.\n"
                       "Pseudonymisé ne veut pas dire anonymisé. Le droit de la protection des données continue de s'appliquer.\n"
                       "`ausgang.json`, `history/` et l'enregistrement contiennent le texte d'avant une pseudonymisation.\n"
                       "Les documents ne constituent pas un conseil juridique.",

    # ---- 1a Protocole de transcription ----
    "p.titel": "Protocole de transcription",
    "p.einleitung": "Le protocole consigne la production de cette transcription et l'ampleur de sa révision manuelle. Les indications proviennent de la transcription et de son journal.",
    "p.transkript": "Transcription", "p.maschine": "Transcription automatique", "p.hand": "Révision manuelle",
    "p.eingriff": "Intervention sur la transcription automatique", "p.dateien": "Fichiers",
    "p.software": "Logiciels et modèles",
    "f.name": "Nom dans la bibliothèque", "f.quelldatei": "Fichier source", "f.dauer": "Durée de la transcription",
    "f.sprache": "Langue (réglage)", "f.segmente": "Segments", "f.sprecher": "Locuteurs (version finale)",
    "f.memos": "Mémos", "f.zotero": "Zotero", "zotero.ja": "liée", "zotero.nein": "non liée",
    "f.datum": "Date du traitement", "f.app": "Application", "f.erkennung": "Reconnaissance vocale",
    "f.vad": "Détection d'activité vocale", "f.trennung": "Séparation des locuteurs", "f.ort": "Lieu du traitement",
    "app.vorgaenger": "{name} {version} (ancien nom de ResearchTranscript ; la numérotation a recommencé à 0.4.0)",
    "erkennung.wert": "whisper.cpp {whisper}, modèle `{modell}` ({herkunft})",
    "erkennung.alt": "whisper.cpp, modèle `{modell}` ; version du programme non consignée lors du traitement",
    "modell.mitgeliefert": "fourni avec l'application", "modell.eigen": "modèle propre aux chercheuses et chercheurs",
    "modell.unbekannt": "provenance non consignée",
    "vad.an": "Silero VAD {silero} dans whisper.cpp", "vad.aus": "non utilisée",
    "vad.diar": "non utilisée ; la séparation des locuteurs découpe les blocs",
    "diar.aus": "désactivée",
    "diar.an": "SpeakerKit (Argmax), modèles pyannote segmentation-3.0, WeSpeaker ResNet34 et pyannote community-1, convertis en Core ML par Argmax. Locuteurs : {zahl}",
    "diar.auto": "automatique", "diar.schwelle": "seuil de regroupement {wert}",
    "ort.neu": "en local sur le Mac ; reconnaissance vocale dans un programme auxiliaire du paquet de l'application",
    "ort.alt": "en local sur le Mac",
    "p.importiert": "Cette transcription a été importée depuis `{datei}`, et non transcrite dans l'application. L'état initial est le fichier tel qu'il a été reçu.",
    "f.sitzungen": "Séances de révision", "f.zeitraum": "Période", "f.wer": "Révisé par (séances)",
    "f.rolle": "Rôle de ces personnes", "f.abgehoert": "Réécoute de l'enregistrement",
    "f.regeln": "Règles de transcription", "f.pseudonym": "Pseudonymisation",
    "sitzungen.text": "{n} (modifications enregistrées à la suite par une même installation, à moins de dix minutes d'intervalle)",
    "wer.eintrag": "{wer} ({n})", "wer.install": "installation {kennung}",
    "offen.rolle": "[ … ]", "offen.abgehoert": "[ entière / partielle / aucune ]",
    "offen.regeln": "[ … ] (p. ex. Dresing & Pehl, simples ou étendues)",
    "offen.pseudonym": "[ … ] (éléments remplacés, règle suivie)",
    "e.journal": "Selon le journal, par segment",
    "e.journal.text": "Le journal note, par séance, les segments modifiés. Sont comptés les segments distincts ; pour plusieurs modifications d'un segment dans une séance, la dernière compte. Les parts sont donc des valeurs minimales.",
    "e.j.text": "Texte modifié", "e.j.sprecher": "Locuteur réattribué", "e.j.zeit": "Temps modifié",
    "e.j.summe": "Segments avec au moins une modification",
    "e.j.weitere": "En outre : {neu} entrées créées, {weg} supprimées, {name} locuteurs renommés.",
    "e.wort": "Par rapport à l'état initial automatique, par mot",
    "e.wort.fehlt": "Un taux par mot ne peut pas être calculé pour cette transcription. Elle a été produite avec une version qui ne conservait pas encore l'état brut automatique.",
    "e.wort.verlauf": "L'état initial provient de l'état non révisé le plus ancien de l'historique.",
    "mass.kopf": "Mesure", "mass.basis": "Base",
    "mass.norm": "Taux de correction, normalisé", "mass.orth": "Taux de correction, orthographique",
    "mass.sdi": "{s} remplacés, {d} supprimés, {i} insérés ; {n} mots dans la version finale",
    "mass.sprechzeit": "Temps de parole réattribué",
    "mass.sprechzeit.basis": "temps de parole commun aux deux états {zeit} ; {a} locuteurs dans l'état initial, {b} dans la version finale",
    "mass.mehrheit": "dont hors locuteurs fusionnés",
    "mass.mehrheit.text": "la fusion de deux voix ne compte pas ici",
    "mass.ohne_maschine": "la machine n'a attribué aucun locuteur",
    "mass.definition": "Taux de correction = (mots remplacés + supprimés + insérés) ÷ mots de la version finale. Comptage comme pour le taux d'erreur de mots, version finale comme référence, alignement par segment. *Normalisé* : en minuscules, sans ponctuation ni caractères spéciaux. *Orthographique* : tel qu'écrit. Temps de parole réattribué = part du temps de parole commun aux deux états dont le locuteur diffère, dans la meilleure correspondance un à un.",
    "mass.vorbehalt": "Mesure d'intervention, et non une mesure d'exactitude. Elle compte toute modification manuelle, pseudonymisation et lissage compris. Elle ne saisit pas les erreurs passées inaperçues.",
    "dateien.text": "Fichiers du dossier de la transcription, avec SHA-256.",
    "dateien.ausgang": "`ausgang.json` est l'état initial inchangé. Il contient le texte d'avant une pseudonymisation.",
    "software.punkte": "whisper.cpp (MIT) <https://github.com/ggml-org/whisper.cpp>\n"
                       "Whisper large-v3-turbo (OpenAI, MIT) <https://huggingface.co/openai/whisper-large-v3-turbo>\n"
                       "SpeakerKit, Argmax OSS (MIT) <https://github.com/argmaxinc/argmax-oss-swift>\n"
                       "pyannote speaker-diarization-community-1 (CC BY 4.0) <https://huggingface.co/pyannote/speaker-diarization-community-1>\n"
                       "Silero VAD (MIT) <https://github.com/snakers4/silero-vad>\n"
                       "ResearchTranscript (AGPL-3.0-or-later) <https://github.com/bias-city/ResearchTranscript>",

    # ---- 1b Paragraphe pour la partie méthodes ----
    "a.titel": "Paragraphe pour la partie méthodes",
    "a.einleitung": "À reprendre et à adapter. Les passages entre crochets sont à remplacer. Le paragraphe vaut pour cette seule transcription.",
    "a.kurz": "Version courte", "a.lang": "Version détaillée, pour une annexe ou un plan de gestion des données",
    "a.app.neu": "ResearchTranscript {version}", "a.app.alt": "{name} {version} (aujourd'hui ResearchTranscript)",
    "a.s1": "L'enregistrement (durée {dauer}) a été transcrit en local avec {app} [ sur un ordinateur du groupe de recherche ] ; l'application ne transmet alors aucune donnée.",
    "a.s2": "La reconnaissance vocale a utilisé whisper.cpp avec le modèle {modell}.",
    "a.s3": "Les locuteurs ont été séparés par SpeakerKit avec des modèles pyannote.",
    "a.s4": "La transcription brute a été vérifiée [ par qui ] [ entièrement / par sondage ] en regard de l'enregistrement, puis corrigée selon [ règles de transcription ] [ et pseudonymisée dans le texte ].",
    "a.s5.wort": "Le taux de correction au niveau des mots était de {norm} (normalisé, version finale comme référence){sprechzeit}.",
    "a.s5.sprechzeit": " ; {wert} du temps de parole ont été réattribués à la main",
    "a.s5.journal": "Selon le journal, le texte a été modifié dans au moins {text} des segments et le locuteur réattribué dans {sprecher}.",
    "a.s6": "Ces valeurs mesurent l'intervention, et non l'exactitude.",
    "a.k1": "L'enregistrement a été transcrit en local avec {app} (whisper.cpp, modèle {modell}), puis vérifié [ par qui ] en regard de l'enregistrement et corrigé.",
    "a.offen": "Reste à compléter",
    "a.offen.punkte": "Qui a corrigé, et si l'ensemble a été réécouté.\n"
                      "Selon quelles règles de transcription le travail a été fait.\n"
                      "Ce qui a été pseudonymisé et selon quelle règle.",
    "a.zitieren": "Citer",
    "a.zitieren.text": "Pohl, B. ({jahr}). ResearchTranscript (version {v}) [Logiciel]. B/IAS – Basel Institut für angewandte Stadtforschung. <https://bias.city/researchtranscript/> Le fichier `researchtranscript.bib` du dossier `{zitieren}` contient cette entrée et les modèles, pour Zotero.",

    # ---- 2a Faits sur l'application ----
    "t.titel": "ResearchTranscript : faits pour la protection des données et la demande d'éthique",
    "t.einleitung": "Faits sur l'application, à reprendre dans un registre des activités de traitement, une analyse d'impact relative à la protection des données ou une demande d'éthique. Identiques pour toutes les transcriptions. Valables pour ResearchTranscript {v} ; pour un traitement plus ancien, voir le protocole de transcription.",
    "t.schritte": "Ce que l'application fait d'un enregistrement", "t.schritt": "Étape", "t.werkzeug": "Outil", "t.wo": "Où",
    "t.schritte.zeilen": "Lire la piste audio, la convertir en 16 kHz mono :: macOS AVFoundation :: en local, dans l'application\n"
                         "Séparation des locuteurs, désactivable :: SpeakerKit (Argmax) avec des modèles pyannote et WeSpeaker, Core ML :: en local, dans l'application\n"
                         "Reconnaissance vocale :: whisper.cpp {whisper}, modèle au choix ; sans séparation des locuteurs, avec Silero VAD {silero} :: en local, programme auxiliaire du paquet de l'application, processeur graphique\n"
                         "Correction dans l'éditeur, avec historique et journal :: ResearchTranscript :: en local\n"
                         "Export vers des formats de texte, de tableau et d'archive ; MP3 via LAME :: ResearchTranscript :: en local, dans le dossier choisi",
    "t.schutz": "Mesures de protection offertes par l'application",
    "t.schutz.punkte": "App Sandbox de macOS : accès aux seuls dossiers choisis dans le dialogue et aux fichiers glissés-déposés.\n"
                       "Pas de serveur, pas de port ouvert, pas de compte.\n"
                       "Enregistrement des modifications en une seule étape ; avant chacun, un état dans l'historique (30 états).\n"
                       "Supprimer déplace vers la corbeille de la bibliothèque, rien n'est perdu sur-le-champ.\n"
                       "Journal par transcription : qui (identifiant de l'installation, adresse e-mail facultative) a modifié quoi et quand.\n"
                       "Zotero est seulement lu, et seulement après autorisation.\n"
                       "Code source ouvert, application signée.",
    "t.nicht": "Ce que l'application ne fait pas",
    "t.nicht.punkte": "Elle ne transmet ni enregistrements, ni textes, ni données d'utilisation : ni télémétrie, ni vérification des mises à jour, ni rapports de plantage propres. L'autorisation réseau de macOS est activée car la vue web intégrée l'exige ; un pare-feu montre qu'aucune connexion ne s'établit. Les rapports de plantage de macOS suivent les réglages du système.\n"
                      "Elle ne télécharge ni modèles ni composants de programme.\n"
                      "Les modèles n'apprennent rien des enregistrements.\n"
                      "Elle ne résume rien et ne reformule rien. La reconnaissance vocale est un modèle d'IA et peut poser des mots qui n'ont pas été dits ; d'où la vérification en regard de l'enregistrement.",
    "t.ablage": "Où se trouvent les données",
    "t.ablage.punkte": "Dans le dossier de bibliothèque choisi, un sous-dossier par transcription : `transkript.json` (texte, locuteurs, mémos, journal, indications Zotero), une copie de l'enregistrement, pour une vidéo le fichier vidéo, `wellenform.json`.\n"
                       "`ausgang.json` conserve l'état tel que la machine ou un fichier importé l'a livré. `history/` conserve les 30 derniers états. Tous deux contiennent le texte d'avant une pseudonymisation.\n"
                       "Les transcriptions supprimées restent dans le dossier `_papierkorb` jusqu'à ce qu'il soit vidé dans le Finder.\n"
                       "Pendant un traitement, des copies de travail du son se trouvent dans le dossier temporaire de l'application.\n"
                       "Les réglages et le journal de l'application se trouvent dans le conteneur de l'application du compte utilisateur. Ce journal contient horodatages, commandes, noms de dossiers et de fichiers, messages d'erreur.",
    "t.person": "Ce que l'application enregistre sur les chercheuses et chercheurs",
    "t.person.punkte": "Un identifiant de l'installation, aléatoire, sans lien avec l'appareil ni la personne.\n"
                       "En option, une adresse e-mail. Tous deux figurent dans le journal de chaque transcription et accompagnent le dossier enrich.",
    "t.export": "Ce que contiennent les exports",
    "t.export.punkte": "Tous les formats de texte (VTT, CSV, TXT, Markdown, Word) : texte, noms des locuteurs, repères temporels. CSV, Markdown et Word : en plus les mémos.\n"
                       "Markdown et Word : en cas de lien Zotero, un en-tête avec titre, date, clé de citation et les personnes dont les rôles ont été choisis.\n"
                       "REFI-QDA (`.qdpx.zip`) : texte, mémos et enregistrement audio, donc la voix ; sur demande le fichier vidéo.\n"
                       "Dossier enrich (`.enrich`) : texte, enregistrement audio en MP3, journal avec identifiant et adresse e-mail, indications Zotero. Pas de mémos.",

    # ---- 2b Indications du responsable du traitement ----
    "s.titel": "Indications du responsable du traitement",
    "s.einleitung": "L'application ne peut pas connaître ces indications. Sans elles, une entrée au registre des activités de traitement est incomplète.",
    "s.felder": "Responsable du traitement :: institution, direction du projet, contact\n"
                "Conseil à la protection des données :: personne ou service compétent\n"
                "Finalité :: projet de recherche, question de recherche\n"
                "Base légale, droit applicable :: selon l'institution, droit cantonal, droit fédéral ou RGPD\n"
                "Personnes concernées :: personnes interrogées, tiers mentionnés, les chercheuses et chercheurs eux-mêmes (journal)\n"
                "Catégories de données personnelles :: voix, propos, le cas échéant données sensibles\n"
                "Destinataires :: qui reçoit des enregistrements, des transcriptions ou des exports\n"
                "Communication à l'étranger :: aucune par l'application ; possible par une transmission ou un stockage dans le cloud\n"
                "Conservation et suppression :: délais, également pour la corbeille, l'historique, l'état initial, les sauvegardes\n"
                "Emplacement de la bibliothèque :: disque interne, volume chiffré, lecteur réseau\n"
                "Sauvegarde et synchronisation :: Time Machine, iCloud Drive et d'autres englobent le dossier s'il s'y trouve\n"
                "Protection de l'appareil :: FileVault, verrouillage de l'écran, comptes utilisateur séparés\n"
                "Personnes autorisées :: qui travaille sur l'ordinateur et dans le dossier\n"
                "Information et consentement :: couvrent-ils l'enregistrement, la transcription, la conservation, la transmission",
    "s.achten": "Points d'attention",
    "s.achten.punkte": "« Local » est une propriété de l'application, non de l'emplacement de stockage. Un dossier synchronisé transmet les données.\n"
                       "C'est le texte de la version finale qui est pseudonymisé. L'enregistrement, l'état initial et l'historique contiennent toujours la voix et les noms réels.\n"
                       "Les modèles propres aux chercheuses et chercheurs ne font pas partie de la liste documentée de l'application.",
    "s.entfernen": "Retirer entièrement un entretien",
    "s.entfernen.text": "Par exemple après un retrait du consentement. L'application ne supprime rien définitivement ; ces emplacements sont à vérifier un à un.",
    "s.entfernen.punkte": "Supprimer la transcription dans l'application, puis vider dans le Finder le dossier `_papierkorb` de la bibliothèque, et la corbeille de macOS.\n"
                          "Les exports, à tous les endroits où ils ont été enregistrés ou transmis.\n"
                          "Les sauvegardes et les copies synchronisées du dossier de la bibliothèque.\n"
                          "L'enregistrement original en dehors de la bibliothèque.\n"
                          "Pour ne retirer que le texte d'avant la pseudonymisation, supprimer `ausgang.json` et `history/`. Ensuite, aucune mesure d'intervention par mot ne peut plus être calculée.",

    # ---- 3 Dépôt des données ----
    "r.status": "Statut", "r.st.pflicht": "obligatoire", "r.st.empfohlen": "recommandé", "r.st.optional": "facultatif",
    "r.vorschlag": "proposition tirée de Zotero, à vérifier",
    "d.titel": "Fiche : indications sur le jeu de données",
    "d.einleitung": "À remplir une fois par jeu de données, même s'il comprend plusieurs entretiens. L'ordre et les noms des champs suivent le formulaire de Zenodo ; le statut se rapporte à Zenodo et à DataCite 4.",
    "d.zeilen": "Resource type :: pflicht :: Dataset :: Transcriptions avec leur documentation.\n"
                "Title :: pflicht :: [ … ] :: Descriptif, sans nom de personne interrogée.\n"
                "Publication date :: pflicht :: [ … ] :: Date de la publication, non de l'entretien.\n"
                "Creators :: pflicht :: {creators} :: Les chercheuses et chercheurs, avec ORCID et institution. Jamais les personnes interrogées.\n"
                "Description :: empfohlen :: [ … ] :: De quoi il s'agit, qui a été interrogé (en termes généraux), dans quel but.\n"
                "Licence :: pflicht :: [ … ] :: Obligatoire chez Zenodo pour les fichiers ouverts. Pour les fichiers sensibles, un contrat d'utilisation au lieu d'une licence ouverte.\n"
                "Access :: pflicht :: [ … ] :: Vaut chez Zenodo par entrée. Documentation ouverte et transcriptions restreintes comme entrées distinctes, reliées entre elles.\n"
                "Contributors :: empfohlen :: [ … ] :: Rôles selon DataCite, p. ex. ContactPerson, DataCollector, RightsHolder.\n"
                "Keywords :: empfohlen :: [ … ] :: Trois à huit termes, si possible issus d'un vocabulaire spécialisé.\n"
                "Languages :: optional :: {sprachen} :: Code ISO de la langue de l'entretien.\n"
                "Dates (Collected) :: empfohlen :: [ … ] :: Période de collecte. En cas de doute, seulement l'année.\n"
                "Version :: optional :: 1.0 :: Après des corrections, une nouvelle version.\n"
                "Funding :: optional :: [ … ] :: Bailleur de fonds et numéro de l'octroi.\n"
                "Related works :: empfohlen :: {dois} :: DOI des articles qui reposent sur les données.",
    "d.befragte": "Les personnes de la partie interrogée figurant dans Zotero ne sont délibérément pas mentionnées.",
    "d.archiv": "Ce que les archives spécialisées demandent en plus",
    "d.archiv.punkte": "Méthode de collecte, p. ex. entretien semi-directif.\n"
                       "Population de référence et sélection des personnes interrogées.\n"
                       "Matériel d'accompagnement : guide d'entretien, feuille d'information, modèle de consentement, rapport méthodologique.",
    "i.titel": "Fiche : indications sur cet entretien",
    "i.einleitung": "Ce que l'application sait de cet entretien précis, et ce qui s'y ajoute pour le dépôt.",
    "i.umfang": "Étendue", "i.umfang.wert": "durée {dauer}, {segmente} segments, {sprecher} locuteurs",
    "i.sprache": "Langue", "i.jahr": "Année de collecte", "i.verfahren": "Procédé de transcription",
    "i.verfahren.wert": "{app}, whisper.cpp, modèle {modell} ; en local ; révisé à la main (voir le protocole de transcription)",
    "i.konventionen": "Conventions de transcription",
    "i.konventionen.wert": "Repères temporels hh:mm:ss par énoncé, locuteur comme indication distincte ; [ compléter les règles ]",
    "i.pseudonym": "Pseudonymisation", "i.pseudonym.wert": "[ … ] (la table de correspondance n'est jamais déposée)",
    "i.formate": "Fichiers pour le dépôt",
    "i.formate.punkte": "La transcription dans un format texte ouvert (TXT, Markdown, CSV), en plus de Word et de REFI-QDA. Calculer les sommes de contrôle après l'export.\n"
                        "REFI-QDA est un format d'échange, avec des pertes possibles d'un programme à l'autre, et non un format d'archivage à lui seul.\n"
                        "La version d'archivage de l'enregistrement est le fichier original, non réencodé. Le MP3 des paquets de l'application est une copie d'usage.\n"
                        "L'en-tête des exports Markdown et Word nomme les personnes choisies dans Zotero. À vérifier avant le dépôt.\n"
                        "Le protocole de transcription peut être joint. `ausgang.json` et `history/` restent en dehors.",
    "e.titel": "Points de contrôle avant une publication",
    "e.einleitung": "Seuls les chercheuses et chercheurs peuvent répondre à ces points. Ce qui ne s'applique pas est noté comme tel.",
    "e.punkt": "Point de contrôle", "e.ja": "rempli", "e.nz": "sans objet",
    "e.punkte": "Le consentement couvre l'archivage et la réutilisation. :: Sinon, consulter la commission d'éthique ou le conseil à la protection des données.\n"
                "Le consentement couvre la transmission de l'enregistrement audio. :: La voix est une donnée personnelle.\n"
                "Un avis de la commission d'éthique existe. :: Indiquer le numéro et l'instance.\n"
                "Les caractéristiques directes et indirectes ainsi que les tiers mentionnés ont été vérifiés. :: Attention aux combinaisons telles que profession, lieu et âge.\n"
                "Titre, description, mots-clés et noms de fichiers ne nomment personne. :: Chez Zenodo, les métadonnées sont toujours publiques.\n"
                "La table de correspondance des pseudonymes est conservée séparément. :: Elle n'a jamais sa place dans le dépôt.\n"
                "L'entrepôt convient aux données. :: Pour les données sensibles, une archive spécialisée avec contrôle d'accès.\n"
                "Les exigences du bailleur de fonds et de la haute école ont été vérifiées. :: Motiver les exceptions à l'accès ouvert dans le plan de gestion des données.",
    "o.titel": "Entrepôts, formats, exigences",
    "o.einleitung": "Identiques pour toutes les transcriptions. Ces indications ne remplacent pas le conseil de l'archive.",
    "o.zenodo": "Ce que Zenodo exige",
    "o.zenodo.punkte": "Les données personnelles sensibles doivent, avant toute diffusion ouverte, être anonymisées de manière appropriée ou couvertes par un consentement. Pour les données sensibles non anonymisées, Zenodo renvoie à des plateformes spécialisées. La responsabilité incombe à la personne qui dépose les fichiers.\n"
                       "Les métadonnées sont toujours publiques, même lorsque les fichiers sont restreints.\n"
                       "Une entrée DOI publiée ne peut pas être supprimée sans laisser de trace.\n"
                       "Limites : 50 Go et 100 fichiers par entrée.",
    "o.repos": "Entrepôts", "o.repo": "Entrepôt", "o.fuer": "Adéquation",
    "o.repos.zeilen": "Zenodo :: Généraliste, DOI immédiat. Pour la documentation, les instruments et les textes réellement anonymisés, pas pour les enregistrements. :: https://zenodo.org\n"
                      "SWISSUbase :: Suisse. Accepte les données qualitatives et sensibles, avec contrôle d'accès et contrat d'utilisation. DOI. :: https://www.swissubase.ch\n"
                      "Qualiservice :: Allemagne, données qualitatives. Conseil, aide à l'anonymisation, accès sur demande. DOI. :: https://www.qualiservice.org\n"
                      "AUSSDA :: Autriche, sciences sociales. Directive propre pour les données qualitatives. :: https://aussda.at\n"
                      "UK Data Service :: Royaume-Uni. Accès gradué. :: https://ukdataservice.ac.uk",
    "o.vorgaben": "Exigences et guides",
    "o.vorgaben.punkte": "Zenodo, champs : <https://help.zenodo.org/docs/deposit/describe-records/>\n"
                         "Zenodo, politiques et conditions : <https://about.zenodo.org/policies/> · <https://about.zenodo.org/terms/>\n"
                         "DataCite Metadata Schema 4 : <https://schema.datacite.org>\n"
                         "SWISSUbase et FORS, déposer des données : <https://forscenter.ch/deposit-data/>\n"
                         "FORS Guide n° 20, anonymisation des données qualitatives : <https://doi.org/10.24449/FG-2023-00020>\n"
                         "Qualiservice, partager des données : <https://www.qualiservice.org/de/daten-teilen.html>\n"
                         "CESSDA Data Management Expert Guide : <https://dmeg.cessda.eu>\n"
                         "FNS, Open Research Data : <https://www.snf.ch/de/FAiWVH4WvpKvohw9/thema/forschungsdaten>\n"
                         "DFG, gestion des données de recherche : <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>\n"
                         "Modèle de README de l'université Cornell (CC0) : <https://data.research.cornell.edu/data-management/sharing/readme/>",
}
