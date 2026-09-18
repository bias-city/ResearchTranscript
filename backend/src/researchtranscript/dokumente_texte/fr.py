"""Textes des documents d'accompagnement — français. Clés et paramètres identiques à de.py."""

T = {
    # ---- général ----
    "feld": "Champ", "wert": "Valeur", "datei": "Fichier", "groesse": "Taille", "nachweise": "Références",
    "nicht_aufgezeichnet": "non consigné", "dezimal": ",",
    "kopf.erzeugt": "Généré par ResearchTranscript {v} le {datum}. Les champs ouverts sont marqués `[ … ]` "
                    "et sont à remplir par les chercheuses et chercheurs.",
    "modell.mitgeliefert": "fourni avec l'application", "modell.eigen": "modèle propre à l'équipe de recherche",
    "modell.unbekannt": "provenance non consignée",
    "modell.heute": "— provenance selon l'état actuel de l'installation, non consignée lors du traitement",
    "diar.aus": "aucune (désactivée)", "diar.an": "SpeakerKit (Argmax) avec pyannote community-1, Core ML",
    "diar.auto": "automatique", "diar.zahl": "nombre de locuteurs :", "diar.trennung": "seuil de regroupement",
    "vad.aus": "non utilisée", "ort.lokal": "en local sur le Mac, dans le processus de l'application ; aucun transfert par l'application",

    "f.kennung": "Identifiant", "f.name": "Nom dans la bibliothèque", "f.quelldatei": "Fichier source",
    "f.dauer": "Durée", "f.sprache": "Langue (réglage)", "f.segmente": "Segments",
    "f.sprecher": "Locuteurs (nombre)", "f.memos": "Mémos (nombre)", "f.datum": "Date du traitement",
    "f.app": "Logiciel", "f.erkennung": "Reconnaissance vocale", "f.modell": "Modèle", "f.modell.satz": "modèle",
    "f.vad": "Détection d'activité vocale", "f.trennung": "Séparation des locuteurs", "f.ort": "Lieu du traitement",
    "f.sitzungen": "Séances de révision selon le journal", "f.zeitraum": "Période de révision",
    "f.journal": "Entrées modifiées selon le journal", "f.wer": "Révisé par",
    "f.abgehoert": "Réécouté en regard de l'enregistrement", "f.regeln": "Règles de transcription",
    "f.pseudonym": "Pseudonymisation",
    "journal.arten": "texte {text} · attribution des locuteurs {sprecher} · temps {zeit} · nouveau {neu} · supprimé {weg} · "
                     "locuteur renommé {name}",
    "offen.wer": "[ … ] (nom ou rôle ; l'application ne le consigne pas)",
    "offen.abgehoert": "[ entièrement / partiellement / non ]",
    "offen.regeln": "[ … ] (p. ex. Dresing & Pehl, simples ou étendues ; règles propres)",
    "offen.pseudonym": "[ … ] (ce qui a été remplacé et selon quelle règle ; la table de correspondance des pseudonymes est conservée séparément)",

    # ---- Dossier de documentation ----
    "paket.ordner": "researchtranscript-documentation", "paket.liesmich": "LISEZMOI",
    "paket.protokolle": "protocoles", "paket.titel": "Dossier de documentation",
    "paket.text": "Documents d'accompagnement des transcriptions choisies, chacun en Markdown et en fichier Word. "
                  "Les champs ouverts `[ … ]` sont à remplir par les chercheuses et chercheurs. Le dossier ne contient "
                  "ni transcriptions ni enregistrements.",
    "paket.bib": "fichier de citations pour Zotero (Fichier › Importer) : le logiciel et toutes les sources mentionnées",

    # ---- 1. Protocole de transcription ----
    "datei.protokoll": "protocole-de-transcription",
    "p.titel": "Protocole de transcription",
    "p.einleitung": "Ce protocole consigne comment la transcription a été produite et dans quelle mesure elle a été "
                    "révisée à la main. Il fait partie de la documentation de l'objet de données individuel et peut "
                    "accompagner le jeu de données. Les indications proviennent du journal de la transcription ; le "
                    "protocole ne mentionne aucun nom de personne enregistrée.",
    "p.aufnahme": "Enregistrement et transcription", "p.maschine": "Transcription automatique",
    "p.importiert": "Cette transcription n'a pas été produite dans l'application, mais importée depuis `{datei}`. "
                    "L'état initial est le fichier tel qu'il a été reçu.",
    "p.hand": "Révision manuelle", "p.mass": "Mesure d'intervention", "p.dateien": "Fichiers",
    "dateien.hinweis": "Fichiers du dossier de la transcription, avec somme de contrôle. `ausgang.json` est l'état "
                       "initial inchangé, par rapport auquel la mesure d'intervention est calculée.",

    "mass.kopf.mass": "Mesure", "mass.kopf.basis": "Base",
    "mass.norm": "Taux de correction au niveau des mots, normalisé",
    "mass.orth": "Taux de correction au niveau des mots, orthographique",
    "mass.sdi": "{s} remplacés, {d} supprimés, {i} insérés ; {n} mots dans la version finale",
    "mass.sprechzeit": "Temps de parole réattribué",
    "mass.sprechzeit.basis": "temps de parole comparé {zeit} ; {a} locuteurs dans l'état initial, {b} dans la version finale",
    "mass.sprechzeit.mehrheit": "dont hors locuteurs fusionnés",
    "mass.sprechzeit.mehrheit.text": "Attribution de plusieurs locuteurs de la machine à la même personne admise : "
                                     "la fusion de deux voix ne compte pas ici",
    "mass.ohne_maschine": "la machine n'a attribué aucun locuteur ; toutes les attributions ont été faites à la main",
    "mass.fehlt": "Pour cette transcription, il n'existe plus d'état initial (créée avant la version 0.6.0, "
                  "l'historique ne remonte plus assez loin). Un taux de correction ne peut pas être calculé. À titre "
                  "indicatif : {n} segments sur {gesamt} ({anteil}) portent la mention « modifié à la main ».",
    "mass.aus_verlauf": "L'état initial provient de l'état le plus ancien de l'historique, que personne n'avait encore révisé.",
    "mass.definition": "**Définitions.** Taux de correction = (mots remplacés + supprimés + insérés) ÷ mots de la "
                       "version finale, calculé comme le taux d'erreur de mots (WER), avec la version finale comme "
                       "référence et l'état initial comme hypothèse. *Normalisé* : en minuscules, sans ponctuation ni "
                       "caractères spéciaux ; trémas et accents sont conservés. *Orthographique* : mots tels "
                       "qu'écrits ; majuscules, minuscules et ponctuation comptent. Temps de parole réattribué = part du "
                       "temps de parole dont le locuteur, dans la version finale, n'est pas le même que dans l'état "
                       "initial, avec la meilleure correspondance un à un possible entre locuteurs ; cela correspond à la "
                       "composante de confusion du Diarization Error Rate, sans fenêtre de tolérance. La parole "
                       "manquée ou détectée à tort n'est pas prise en compte.",
    "mass.vorbehalt": "Mesure d'intervention, et non mesure d'exactitude. Le taux comprend toute modification faite à la "
                      "main, y compris la pseudonymisation, le lissage et l'application des règles de transcription. "
                      "Il ne saisit pas les erreurs que personne n'a remarquées. Il chiffre l'ampleur de la révision — "
                      "non la qualité de la machine ou de la version finale.",

    # ---- 2. Module méthodologique ----
    "datei.methoden": "module-methodologique-transcription",
    "m.titel": "Module méthodologique : transcription",
    "m.einleitung": "Une section méthodologique décrit le corpus, non l'entretien individuel. Ce module résume les "
                    "transcriptions choisies : étendue, procédé et ampleur de la révision manuelle des "
                    "transcriptions automatiques brutes. Suivent un paragraphe à reprendre et "
                    "une liste de ce que seule l'équipe de recherche sait.",
    "m.korpus": "Corpus", "m.n": "Transcriptions", "m.importiert": "dont {n} importées, non transcrites dans l'application",
    "m.gesamt": "Durée totale", "m.mittel": "Durée : moyenne (étendue)",
    "m.eigen": "dont un modèle propre à l'équipe de recherche, qui ne fait pas partie de la liste fournie avec l'application",
    "m.diar": "pour {n} transcriptions sur {gesamt} (SpeakerKit, pyannote community-1)",
    "m.zeitraum": "Période des traitements automatiques",
    "m.mass": "Mesure d'intervention sur le corpus",
    "m.mass.text": "Calculée pour {n} transcriptions sur {gesamt} (pour les autres, il n'existe pas d'état initial).",
    "m.median": "Médiane (étendue)",
    "m.absatz": "Paragraphe pour la section méthodologique",
    "m.absatz.hinweis": "À reprendre et à adapter. Les passages entre crochets sont à remplacer.",
    "m.absatz.text": "Les enregistrements (n = {n} ; durée totale {gesamt} ; moyenne {mittel}, étendue {spanne}) ont été "
                     "transcrits avec ResearchTranscript {version} (B/IAS Bâle, AGPL-3.0) entièrement en local [ sur un "
                     "ordinateur du groupe de recherche ] ; l'application ne transmet alors rien à des services externes. La "
                     "reconnaissance vocale a utilisé whisper.cpp {whisper} avec le modèle {modell} (Radford et al., 2022)."
                     "{diar} Les transcriptions brutes ont ensuite été vérifiées [ entièrement / par échantillonnage ] "
                     "par [ par qui ] en regard de l'enregistrement, corrigées selon [ règles de transcription ] [ et "
                     "pseudonymisées dans le texte ]. Le taux de correction au niveau des mots (calculé comme le taux "
                     "d'erreur de mots, version finale comme référence, normalisé) s'élevait en médiane à {norm}. Le taux "
                     "mesure l'intervention, pseudonymisation comprise, et non l'exactitude.",
    "m.absatz.diar": " Les locuteurs ont été séparés avec SpeakerKit et le modèle pyannote community-1 (Plaquet & "
                     "Bredin, 2023) ; la part du temps de parole réattribué à la main s'élevait en médiane à {sprechzeit}.",
    "m.offen": "Ce que seule l'équipe de recherche sait",
    "m.offen.wer": "Qui a corrigé, avec quelle qualification, et si l'ensemble a été réécouté en regard de l'enregistrement.",
    "m.offen.regeln": "Selon quelles règles de transcription le travail a été fait (verbatim, lissage, pauses, dialecte).",
    "m.offen.pseudonym": "Ce qui a été pseudonymisé et selon quelle règle ; où se trouve la table de correspondance des pseudonymes.",
    "m.offen.einwilligung": "Si le consentement des personnes interrogées couvre le mode de traitement et une transmission ultérieure.",
    "m.je": "Par transcription",

    # ---- 3. Module pour le registre ----
    "datei.verfahren": "module-registre-researchtranscript",
    "v.titel": "Module pour le registre des activités de traitement, l'analyse d'impact relative à la protection des données (AIPD) et la demande d'éthique",
    "v.einleitung": "Ces documents décrivent une activité de traitement ou un projet, non l'enregistrement "
                    "individuel. Le module fournit à cet effet les faits concernant l'application, telle qu'elle est "
                    "installée sur cet ordinateur. Tout ce que seul le responsable du traitement sait figure plus bas "
                    "sous forme de champ ouvert. Le module n'est ni un conseil juridique ni une affirmation sur la licéité.",
    "v.schritte": "Ce que l'application fait d'un enregistrement", "v.schritt": "Étape", "v.werkzeug": "Outil",
    "v.wo": "Où",
    "v.s1.a": "Lire la piste audio et la convertir en 16 kHz mono", "v.s1.b": "macOS AVFoundation",
    "v.s1.c": "en local, dans le processus de l'application",
    "v.s2.a": "Détecter l'activité vocale", "v.s2.b": "Silero VAD {silero} dans whisper.cpp", "v.s2.c": "en local",
    "v.s3.a": "Reconnaissance vocale : du son au texte avec repères temporels",
    "v.s3.b": "whisper.cpp {whisper} (programme auxiliaire dans le paquet de l'application), modèle au choix",
    "v.s3.c": "en local, processeur graphique (Metal)",
    "v.s4.a": "Séparation des locuteurs (désactivable)", "v.s4.b": "SpeakerKit (Argmax) avec pyannote community-1, Core ML",
    "v.s4.c": "en local, Neural Engine",
    "v.s5.a": "Correction dans l'éditeur ; historique et journal par transcription", "v.s5.b": "ResearchTranscript",
    "v.s5.c": "en local",
    "v.s6.a": "Export (VTT, CSV, TXT, Markdown, Word, REFI-QDA, dossier enrich ; MP3 via LAME)",
    "v.s6.b": "ResearchTranscript", "v.s6.c": "en local, dans le dossier choisi par la personne",
    "v.modelle": "Modèles de reconnaissance vocale actuellement disponibles sur cet ordinateur :", "v.herkunft": "Provenance",
    "v.nicht": "Ce que l'application ne fait pas",
    "v.nicht.punkte": "Elle n'établit aucune connexion réseau : pas de compte, pas de télémétrie, pas de vérification des mises à jour, pas de rapports de plantage propres. Elle n'ouvre les liens (déclaration de protection des données, code source) que sur clic, dans le navigateur.\n"
                      "Elle ne télécharge ni modèles ni composants de programme.\n"
                      "Elle n'exploite ni serveur ni service réseau ; le traitement s'exécute dans le processus de l'application.\n"
                      "Elle s'exécute dans l'App Sandbox de macOS et ne lit que les dossiers que la personne a choisis et les fichiers qu'elle y dépose par glisser-déposer.\n"
                      "Elle ne contient aucune IA générative : rien n'est résumé, reformulé ni interprété.\n"
                      "Elle ne lit Zotero qu'après autorisation expresse et ne le modifie jamais.",
    "v.ablage": "Où se trouvent les données",
    "v.ablage.punkte": "Dans le dossier de la bibliothèque, que la personne choisit ; par transcription, un sous-dossier avec `transkript.json`, une copie de l'enregistrement (pour la vidéo, en plus le fichier vidéo) et `wellenform.json`.\n"
                       "`ausgang.json` conserve l'état initial automatique inchangé, `history/` les 30 derniers états précédant chaque enregistrement des modifications. Tous deux contiennent le texte AVANT une pseudonymisation.\n"
                       "Les transcriptions supprimées se trouvent dans le dossier `_papierkorb` de la bibliothèque, jusqu'à ce qu'il soit vidé dans le Finder.\n"
                       "Les réglages et le journal de l'application se trouvent dans le conteneur de l'application du compte utilisateur ; le journal peut contenir des noms de fichiers et des messages d'erreur.\n"
                       "L'application ne sait pas où se trouve le dossier de la bibliothèque, ni s'il est sauvegardé ou synchronisé.",
    "v.export": "Ce que contiennent les exports",
    "v.export.punkte": "VTT, TXT : texte seul. CSV, Markdown, Word : texte et mémos des chercheuses et chercheurs.\n"
                       "REFI-QDA (`.qdpx.zip`) et dossier enrich (`.enrich`) : en plus l'enregistrement audio, donc la voix ; avec une vidéo, sur demande, le fichier vidéo.\n"
                       "Dossier enrich : en outre le journal (avec l'adresse e-mail, si elle est indiquée dans les réglages) et les métadonnées Zotero liées.",
    "v.offen": "À remplir par le responsable du traitement",
    "v.offen.text": "L'application ne peut pas connaître ces indications. Sans elles, l'entrée est incomplète.",
    "v.eintrag": "Entrée", "v.hinweis": "Remarque",
    "v.offen.felder": "Responsable du traitement :: institution, direction du projet, contact\n"
                      "Conseiller ou conseillère à la protection des données :: personne ou service compétent\n"
                      "Finalité du traitement :: projet de recherche, question de recherche\n"
                      "Base légale et droit applicable :: selon l'institution, droit cantonal, droit fédéral ou RGPD ; l'application ne le sait pas\n"
                      "Personnes concernées :: personnes interrogées ; tiers mentionnés dans l'entretien\n"
                      "Catégories de données personnelles :: voix, propos ; le cas échéant, données sensibles\n"
                      "Destinataires :: qui reçoit des enregistrements, des transcriptions ou des exports\n"
                      "Communication à l'étranger :: aucune par l'application ; possible par la transmission d'exports ou un stockage dans le cloud\n"
                      "Conservation et suppression :: délais ; également pour la corbeille, l'historique, l'état initial et les sauvegardes\n"
                      "Emplacement du dossier de la bibliothèque :: disque interne, volume chiffré, lecteur réseau\n"
                      "Sauvegarde et synchronisation :: Time Machine, iCloud Drive, autres services — ils englobent le dossier s'il s'y trouve\n"
                      "Protection de l'appareil :: FileVault, verrouillage de l'écran, comptes utilisateur séparés\n"
                      "Personnes autorisées :: qui peut travailler sur l'ordinateur et dans le dossier\n"
                      "Information et consentement des personnes interrogées :: couvrent-ils l'enregistrement, la transcription, la conservation, la transmission ?",
    "v.warnung": "Points d'attention",
    "v.warnung.punkte": "Pseudonymisé ne veut pas dire anonymisé : des données pseudonymisées restent des données personnelles.\n"
                        "C'est le texte de la version finale qui est pseudonymisé. L'enregistrement, l'état initial et l'historique contiennent toujours la voix et les noms réels ; qui n'en a plus besoin les supprime dans le Finder.\n"
                        "« Local » est une propriété de l'application, non de l'emplacement de stockage : un dossier synchronisé transmet les données.\n"
                        "Les modèles propres à l'équipe de recherche ne font pas partie de la liste fournie et documentée avec l'application.",

    # ---- 4. Fiche de dépôt ----
    "datei.repositorium": "fiche-de-depot",
    "r.dok": "Fiche de dépôt pour entrepôt de données",
    "r.einleitung": "Préparation du dépôt de {n} transcription(s) comme données de recherche avec DOI. Les champs suivent "
                    "DataCite 4 et le formulaire de Zenodo, complétés par ce qu'exigent les archives spécialisées en "
                    "données qualitatives. Ce que l'application connaît par Zotero et par les transcriptions est inscrit "
                    "et marqué comme proposition ; tout le reste est ouvert. La fiche ne remplace ni le conseil de "
                    "l'archive ni un conseil juridique.",
    "r.warnung": "À lire d'abord",
    "r.warnung.punkte": "L'enregistrement audio contient la voix et constitue une donnée personnelle. Il n'est pas publié en accès ouvert, même sous pseudonyme.\n"
                        "Pseudonymisé ne veut pas dire anonyme ; le droit de la protection des données continue de s'appliquer.\n"
                        "Zenodo exige dans ses conditions d'utilisation que les données personnelles sensibles soient, avant toute diffusion ouverte, anonymisées de manière appropriée ou couvertes par un consentement, et renvoie, pour les données sensibles non anonymisées, à des plateformes spécialisées. La responsabilité incombe à la personne qui dépose les fichiers.\n"
                        "Les métadonnées (titre, description, mots-clés, noms de fichiers) sont toujours publiques, même lorsque les fichiers sont restreints. Elles ne doivent contenir aucune donnée personnelle.\n"
                        "Une entrée DOI publiée ne peut pas être supprimée sans laisser de trace.\n"
                        "Les personnes interrogées n'apparaissent jamais comme auteur·e·s. L'application ne propose, à partir de Zotero, que des personnes qui n'appartiennent pas à la partie interrogée ; chaque proposition est à vérifier.\n"
                        "La transcription est produite automatiquement et révisée à la main ; l'état des corrections a sa place dans la documentation (protocole de transcription, module méthodologique).",
    "r.status": "Statut", "r.erlaeuterung": "Explication", "r.vorschlag": "proposition, à vérifier",
    "r.st.pflicht": "obligatoire", "r.st.empfohlen": "recommandé", "r.st.optional": "facultatif",
    "r.st.archiv": "exigé par les archives spécialisées",
    "r.befragte_weg": "(Les personnes de la partie interrogée figurant dans Zotero ne sont délibérément pas mentionnées.)",
    "r.g.beschreibung": "Description", "r.g.personen": "Personnes et rôles", "r.g.rechte": "Droits et accès",
    "r.g.methode": "Contenu et méthode", "r.g.dateien": "Fichiers", "r.g.ethik": "Éthique et protection des données",
    "r.titel": "Titre du jeu de données", "r.titel.e": "Descriptif, sans nom de personne interrogée.",
    "r.typ": "Type de ressource", "r.typ.e": "Un ensemble de transcriptions et de documentation est considéré comme un Dataset.",
    "r.pubdatum": "Date de publication", "r.pubdatum.e": "Date de la publication dans l'entrepôt, non de l'entretien.",
    "r.abstract": "Description", "r.abstract.e": "De quoi il s'agit, qui a été interrogé (en termes généraux) et dans quel but.",
    "r.schlagworte": "Mots-clés", "r.schlagworte.e": "Trois à huit termes, si possible issus d'un vocabulaire spécialisé.",
    "r.sprache": "Langue(s)", "r.sprache.e": "Langue des entretiens, en code ISO.",
    "r.erhebung": "Période de collecte", "r.erhebung.e": "En cas de doute, seulement l'année ou le mois : une date précise peut rendre des personnes identifiables.",
    "r.ort": "Lieu ou région", "r.ort.e": "Seulement avec une précision telle que personne ne soit identifiable.",
    "r.version": "Version", "r.version.e": "Après des corrections, créer une nouvelle version.",
    "r.publisher": "Entrepôt", "r.publisher.e": "Nom de l'entrepôt choisi (automatique pour Zenodo).",
    "r.verwandt": "Publications liées", "r.verwandt.e": "DOI des articles qui reposent sur les données.",
    "r.foerderung": "Financement", "r.foerderung.e": "Bailleur de fonds et numéro de l'octroi ; le FNS et la DFG attendent cette indication.",
    "r.creators": "Auteur·e·s (Creators)", "r.creators.e": "Les chercheuses et chercheurs responsables du jeu de données, avec ORCID et institution. Jamais les personnes interrogées.",
    "r.contributors": "Contributeurs et contributrices avec rôle", "r.contributors.e": "p. ex. DataCollector, ProjectLeader, Supervisor (rôles selon DataCite).",
    "r.kontakt": "Personne de contact", "r.kontakt.e": "Qui répondra aux demandes d'accès, même dans quelques années.",
    "r.rechteinhaber": "Titulaire des droits", "r.rechteinhaber.e": "Le plus souvent la haute école ou les chercheuses et chercheurs.",
    "r.lizenz": "Licence", "r.lizenz.e": "Obligatoire pour les fichiers ouverts, p. ex. CC BY 4.0 pour la documentation ; pour les fichiers sensibles, un contrat d'utilisation au lieu d'une licence ouverte.",
    "r.zugang": "Niveau d'accès par fichier", "r.zugang.e": "Ouvert, restreint ou fermé — séparément pour la documentation, la transcription et l'enregistrement.",
    "r.embargo": "Embargo jusqu'au", "r.embargo.e": "Report motivé, p. ex. jusqu'à la publication.",
    "r.bedingungen": "Conditions pour les demandes d'accès", "r.bedingungen.e": "Qui obtient l'accès, et à quelles conditions.",
    "r.methode": "Méthode de collecte", "r.methode.e": "p. ex. entretien semi-directif, sur place ou en ligne.",
    "r.sampling": "Sélection des personnes interrogées", "r.sampling.e": "Population de référence et mode de sélection.",
    "r.umfang": "Étendue", "r.umfang.e": "Données techniques de base tirées des transcriptions.",
    "r.umfang.wert": "{n} entretien(s), durée totale {dauer}",
    "r.technik": "Procédé de transcription", "r.technik.e": "Produite automatiquement, révisée à la main ; compléter l'état des corrections à partir du module méthodologique.",
    "r.technik.wert": "ResearchTranscript {version}, whisper.cpp {whisper}, modèle {modell} ; en local",
    "r.konventionen": "Conventions de transcription", "r.konventionen.e": "Notation des pauses, des chevauchements, des passages incompréhensibles ; compléter ici ce qui dépasse le format.",
    "r.konventionen.wert": "Repères temporels hh:mm:ss par énoncé, locuteur comme indication distincte ; [ compléter les règles ]",
    "r.anonymisierung": "Anonymisation", "r.anonymisierung.e": "Ce qui a été remplacé et comment ; la table de correspondance des pseudonymes elle-même n'est jamais déposée.",
    "r.begleit": "Matériel d'accompagnement", "r.begleit.e": "Guide d'entretien, feuille d'information, modèle de consentement, rapport méthodologique, README.",
    "r.dateien.text": "Fichiers tels qu'ils se trouvent dans la bibliothèque, avec somme de contrôle (SHA-256). Pour le dépôt, "
                      "des exports en sont tirés ; les sommes de contrôle des exports sont à calculer après l'export.",
    "r.formate": "À propos des formats :",
    "r.formate.punkte": "Déposer les transcriptions, en plus de Word et de REFI-QDA, dans un format texte ouvert (TXT, Markdown, CSV) ; les archives préfèrent les formats simples et ouverts.\n"
                        "REFI-QDA est un format d'échange, avec des pertes possibles d'un programme à l'autre, et non un format d'archivage à lui seul.\n"
                        "Le MP3 des paquets de l'application est une copie d'usage. Comme original d'archivage, les archives recommandent FLAC ou WAV — donc l'enregistrement d'origine.\n"
                        "Chaque transcription a besoin d'un en-tête avec identifiant, date et contexte ; les exports Markdown et Word de l'application l'écrivent.",
    "r.ethik.text": "Seule l'équipe de recherche peut y répondre. Tant qu'un point reste ouvert, rien n'est publié.",
    "r.pruefpunkt": "Point de contrôle", "r.erledigt": "fait",
    "r.ethik.punkte": "Le consentement couvre l'archivage et la réutilisation. :: Sans consentement documenté, pas de transmission.\n"
                      "Le consentement couvre la transmission de l'enregistrement audio. :: La voix est une donnée personnelle.\n"
                      "Un avis ou une condition de la commission d'éthique existe. :: Indiquer le numéro et l'instance.\n"
                      "Les identifiants directs et indirects ainsi que les tiers mentionnés ont été vérifiés. :: Attention aux combinaisons telles que profession, lieu et âge.\n"
                      "Titre, description, mots-clés et noms de fichiers sont exempts de données personnelles. :: Les métadonnées sont toujours publiques.\n"
                      "La table de correspondance des pseudonymes est conservée séparément. :: Elle n'a jamais sa place dans le dépôt.\n"
                      "L'état initial et l'historique restent en dehors. :: `ausgang.json` et `history/` contiennent le texte d'avant la pseudonymisation.\n"
                      "L'entrepôt convient aux données. :: Pour les données sensibles, une archive spécialisée avec contrôle d'accès.\n"
                      "Les exigences du bailleur de fonds et de la haute école ont été vérifiées. :: Motiver les exceptions à l'accès ouvert dans le plan de gestion des données.",
    "r.wohin": "Quel entrepôt", "r.repo": "Entrepôt", "r.repo.fuer": "Adéquation",
    "r.repos": "Zenodo :: Généraliste, DOI immédiat ; fichiers restreignables, métadonnées toujours ouvertes. Pour la documentation, les instruments et les textes réellement anonymisés ; pas pour les enregistrements. :: https://zenodo.org\n"
               "SWISSUbase (FORS) :: Suisse, sciences sociales ; accepte les données qualitatives et sensibles avec contrôle d'accès et contrat d'utilisation ; DOI. :: https://www.swissubase.ch\n"
               "Qualiservice :: Allemagne, données qualitatives ; conseil, aide à l'anonymisation, accès uniquement sur demande ; DOI. :: https://www.qualiservice.org\n"
               "AUSSDA :: Autriche, sciences sociales ; directive propre pour les données qualitatives. :: https://aussda.at\n"
               "UK Data Service :: Royaume-Uni ; accès gradué (open, safeguarded, controlled). :: https://ukdataservice.ac.uk",
    "r.quellen": "Sources",
    "r.quellen.punkte": "DataCite Metadata Schema 4 : <https://schema.datacite.org>\n"
                        "Zenodo : champs <https://help.zenodo.org/docs/deposit/describe-records/>, politiques <https://about.zenodo.org/policies/>, conditions <https://about.zenodo.org/terms/>\n"
                        "CESSDA Data Management Expert Guide : <https://dmeg.cessda.eu>\n"
                        "FORS Guide n° 20, anonymisation des données qualitatives : <https://doi.org/10.24449/FG-2023-00020>\n"
                        "FNS, Open Research Data : <https://www.snf.ch/de/FAiWVH4WvpKvohw9/thema/forschungsdaten>\n"
                        "DFG, gestion des données de recherche : <https://www.dfg.de/de/grundlagen-themen/grundlagen-und-prinzipien-der-foerderung/forschungsdaten>\n"
                        "Modèle de README de l'université Cornell (CC0) : <https://data.research.cornell.edu/data-management/sharing/readme/>",
}
