# ResearchTranscript — Fiche pour les chercheur·euse·s

Ce qu'est l'application, quelle IA y fait quoi, où se trouve le code,
et pourquoi la transcription ne quitte jamais l'ordinateur. À remettre à
une direction de projet, un comité d'éthique ou des collègues. État au
23 septembre 2026, version 0.6.2.

Cette fiche est le modèle général. Depuis la version 0.6.0,
l'application génère elle-même la version propre à chaque transcription
(Éditeur › Export › « Paquet de documentation (.zip) … ») : protocole
de transcription avec le modèle et la version réellement utilisés et
l'ampleur mesurée de la révision manuelle, paragraphe pour la partie
méthodes, faits pour la protection des données, fiche pour le dépôt de
données et fichier de citation.

## Ce que fait l'application

ResearchTranscript transforme des enregistrements audio — entretiens,
discussions de groupe, ateliers — en texte avec codes temporels et
attribution des locuteurs. La transcription est ensuite corrigée dans un
éditeur, les locuteurs sont nommés, les noms remplacés, et le résultat
est exporté pour l'analyse (ATLAS.ti, MAXQDA, NVivo via REFI-QDA ;
enrich ; WebVTT, CSV, texte, Markdown, Word). Les enregistrements vidéo
(MP4/MOV) sont aussi acceptés : le son est extrait, la vidéo reste
inchangée avec la transcription et ne quitte l'ordinateur que si on
l'inclut explicitement dans l'export REFI-QDA. Tout cela se passe sur
son propre Mac.

## Quelle IA fait quoi

| Composant | Tâche | Origine, licence | S'exécute où |
|---|---|---|---|
| whisper.cpp 1.8.2 avec le modèle `large-v3-turbo` | Reconnaissance vocale : audio → texte avec codes temporels | modèle d'OpenAI (MIT), exécution whisper.cpp (MIT) | en local, comme programme auxiliaire du paquet de l'application, sur le processeur graphique du Mac (Metal) |
| Silero VAD 5.1.2 (dans whisper.cpp) | Activité vocale : détecte où l'on parle. Seulement si la séparation des locuteurs est désactivée ; sinon, c'est elle qui découpe les blocs | MIT | en local, dans le même programme auxiliaire |
| SpeakerKit (Argmax) avec les modèles pyannote segmentation-3.0, WeSpeaker ResNet34 et pyannote community-1 | Séparation des locuteurs : détecte les changements de locuteur, chevauchements compris, et regroupe les voix ; désactivable | modèles issus de pyannote speaker-diarization-community-1 (CC BY 4.0), convertis en Core ML par Argmax ; moteur SpeakerKit d'Argmax (MIT) | en local, dans l'application, via Core ML |

Tous les modèles sont contenus dans le paquet de l'application ; elle
ne télécharge ni modèles ni composants de programme (un autre modèle
whisper.cpp peut être déposé à la main dans le dossier « Modelle » de la
bibliothèque ; il ne fait pas partie de cette liste, et le journal de
chaque transcription indique le modèle utilisé). Le son est lu par
macOS lui-même (AVFoundation), le MP3 est écrit par LAME (LGPL, lié
dynamiquement). Il n'y a ni accès à un service d'IA, ni compte, ni clé.

**Ni résumé ni reformulation.** L'application ne résume rien et ne
reformule rien. Les modèles n'apprennent rien des enregistrements.

**Limites de la reconnaissance vocale.** La reconnaissance vocale est
un modèle d'IA. Là où il ne comprend rien (bruits de fond, dialecte,
chevauchements), il peut poser des mots qui n'ont pas été dits. Une
transcription issue de ResearchTranscript est une **transcription
brute** qui doit être vérifiée en regard de l'enregistrement ; l'éditeur
est conçu pour cela. L'allemand standard, le français, l'italien et
l'anglais sont bien reconnus, le suisse allemand de façon lacunaire —
les locuteurs sont néanmoins séparés proprement.

## Où se trouve le code

- Code source : <https://github.com/bias-city/ResearchTranscript>
- Licence : AGPL-3.0-or-later, avec une permission additionnelle pour
  la distribution par l'App Store — logiciel libre, qui peut être
  utilisé, examiné, modifié et redistribué
- Développé au B/IAS – Basel Institut für angewandte Stadtforschung,
  Beckenweg 6, 4056 Bâle, <https://bias.city>
- Paquet d'installation (DMG) : signé et notarisé avec un Apple
  Developer ID, publié avec les versions sur GitHub, avec somme de
  contrôle
- Qui ne fait pas confiance au binaire : le dépôt contient toute la
  chaîne de construction, l'application peut être compilée soi-même

## La transcription ne quitte pas l'ordinateur

- L'application ne transmet **ni enregistrements, ni textes, ni données
  d'utilisation** : ni compte, ni télémétrie, ni vérification des mises
  à jour, ni rapports de plantage propres, ni téléchargement de
  modèles. L'autorisation réseau de macOS n'est activée que parce que
  la vue web intégrée l'exige ; un pare-feu ou `nettop` montre
  qu'aucune connexion ne s'établit.
- Il n'y a pas de service interne : pas de serveur, pas de port ouvert.
  La logique de l'application s'exécute, intégrée, dans l'application
  elle-même. Lisible par tout le monde : le shell
  `frontend/src-tauri/src/lib.rs` ne démarre aucun serveur et n'ouvre
  aucun port.
- L'application s'exécute dans l'App Sandbox de macOS : accès aux seuls
  dossiers choisis dans un dialogue et aux fichiers glissés-déposés.
  Les autorisations figurent dans
  `frontend/src-tauri/entitlements.plist`.
- Enregistrement et transcription se trouvent dans le dossier de
  bibliothèque choisi, un sous-dossier par transcription :
  `transkript.json` (texte, locuteurs, mémos, journal, indications
  Zotero), une copie de l'enregistrement, pour une vidéo aussi le
  fichier vidéo, `wellenform.json`, ainsi que `ausgang.json` (l'état tel
  que la machine ou un fichier importé l'a livré) et `history/` (les
  30 derniers états). Ce qui est supprimé reste dans le dossier
  `_papierkorb` de la bibliothèque jusqu'à ce qu'il soit vidé dans le
  Finder. Les réglages et le journal de l'application se trouvent dans
  le conteneur de l'application du compte utilisateur.
- Pas de service cloud, pas de compte utilisateur, pas de
  sous-traitant, pas de transfert vers un pays tiers — parce que rien
  n'est transmis.

Ce que cela ne couvre **pas** : les sauvegardes du Mac (Time Machine,
iCloud Drive pour le dossier Documents) et les rapports de plantage de
macOS lui-même suivent les réglages système, pas l'application. Qui
place le dossier de bibliothèque dans un dossier synchronisé synchronise
les enregistrements.

## Pseudonymiser les noms

- **Renommer les locuteurs :** un nom dans le panneau des locuteurs vaut
  pour tous les segments de cette personne — « Locuteur 1 » devient
  « B3 » en une étape.
- **Noms dans le texte :** « Rechercher et remplacer » trouve un nom
  dans tous les segments, montre chaque occurrence dans son contexte et
  remplace une par une ou toutes d'un coup — même là où la transcription
  a coupé le nom en fin de ligne.
- **Ce que l'application ne décide pas :** quelles informations
  remplacer — lieux, employeurs, événements. Cela reste la décision de
  la personne qui fait la recherche.
- **L'enregistrement reste ce qu'il est.** C'est le texte de la version
  finale qui est pseudonymisé. `ausgang.json` et `history/` contiennent
  le texte d'avant une pseudonymisation, l'enregistrement la voix et
  les noms réels.
- **Ce que contiennent les exports.** Tous les formats de texte (VTT,
  CSV, TXT, Markdown, Word) : texte, noms des locuteurs, repères
  temporels ; CSV, Markdown et Word : en plus les mémos ; Markdown et
  Word, en cas de lien Zotero, un en-tête avec titre, date, clé de
  citation et les personnes dont les rôles ont été choisis. REFI-QDA
  (`.qdpx.zip`) : texte, mémos et enregistrement audio, donc la voix ;
  sur demande le fichier vidéo. Dossier enrich (`.enrich`) : texte,
  enregistrement audio en MP3, journal (identifiant de l'installation,
  adresse e-mail facultative), indications Zotero ; pas de mémos. Qui
  ne veut transmettre que des données pseudonymisées transmet un format
  de texte et vérifie mémos et en-tête.

## Pour la partie méthodes

> Les enregistrements ont été transcrits en local avec
> ResearchTranscript 0.6.2 (B/IAS Bâle, AGPL-3.0-or-later ;
> reconnaissance vocale whisper.cpp avec le modèle large-v3-turbo,
> séparation des locuteurs par SpeakerKit avec des modèles pyannote) sur
> un ordinateur du groupe de recherche ; l'application ne transmet alors
> aucune donnée. Les transcriptions brutes ont ensuite été vérifiées en
> regard de l'enregistrement, corrigées et pseudonymisées dans le texte.

---

Source : <https://github.com/bias-city/ResearchTranscript> (dossier
`site/docs`). La fiche est publiée sous CC BY 4.0 : utilisation et
adaptation libres, y compris commerciales, à condition de citer B/IAS
et d'indiquer les modifications.
