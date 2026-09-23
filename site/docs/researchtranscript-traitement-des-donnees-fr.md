# ResearchTranscript — Description du traitement des données

Bloc de texte à insérer dans un registre des activités de traitement,
une analyse d'impact relative à la protection des données, une demande
au comité d'éthique ou un plan de gestion des données. État au
23 septembre 2026, ResearchTranscript 0.6.2. Les mentions entre
`[crochets]` sont complétées par le responsable du traitement.

Ce texte décrit ce que le logiciel fait et ne fait pas. La
qualification juridique de son propre traitement — au regard du RGPD ou
de la nLPD suisse — revient au responsable du traitement ; le texte ne
remplace pas un avis juridique.

Ce texte est le modèle général. Depuis la version 0.6.0, l'application
génère elle-même la version propre à chaque transcription (Éditeur ›
Export › « Paquet de documentation (.zip) … ») : protocole de
transcription avec le modèle et la version réellement utilisés et
l'ampleur mesurée de la révision manuelle, paragraphe pour la partie
méthodes, faits pour la protection des données, fiche pour le dépôt de
données et fichier de citation.

---

## 1. Logiciel utilisé

ResearchTranscript, version `[0.6.2]`. Logiciel libre sous
AGPL-3.0-or-later (avec une permission additionnelle pour la
distribution par l'App Store), développé au B/IAS – Basel Institut für
angewandte Stadtforschung. Code source public :
<https://github.com/bias-city/ResearchTranscript> ; le paquet
d'installation (DMG), signé et notarisé, y est publié avec les
versions. Le logiciel fonctionne comme application locale sous macOS
(Apple Silicon), dans l'App Sandbox de macOS, et est installé et
exploité par le responsable du traitement lui-même.

## 2. Finalité du traitement

Conversion d'enregistrements audio `[p. ex. entretiens semi-directifs
dans le projet …]` en texte avec codes temporels et attribution des
locuteurs, en vue d'une analyse qualitative ultérieure `[dans ATLAS.ti /
MAXQDA / NVivo / enrich / …]`.

## 3. Personnes concernées et catégories de données

Les personnes concernées sont les personnes enregistrées `[personnes
interrogées, participant·e·s à des discussions de groupe, …]`. Sont
traités les enregistrements vocaux (voix et contenu de l'échange) ainsi
que les transcriptions qui en sont produites, avec codes temporels et
attribution des locuteurs. Selon le contenu, des catégories
particulières de données personnelles peuvent être concernées
`[oui / non : …]`.

## 4. Flux de données d'une transcription

1. **Entrée.** Le fichier audio ou vidéo est lu depuis le système de
   fichiers local de l'appareil (audio : MP3, WAV, M4A, OGG, FLAC ;
   vidéo : MP4, MOV, M4V en H.264/HEVC — d'une vidéo seule la piste
   audio est lue, la vidéo n'est jamais convertie). Le son est lu par
   macOS AVFoundation. L'App Sandbox de macOS ne permet l'accès qu'aux
   dossiers choisis par la personne dans un dialogue et aux fichiers
   glissés-déposés.
2. **Traitement.** La logique de l'application s'exécute, intégrée,
   dans l'application elle-même. La reconnaissance vocale (whisper.cpp
   1.8.2, modèle large-v3-turbo) s'exécute comme programme auxiliaire
   du paquet de l'application, sur le processeur graphique (Metal). La
   séparation des locuteurs (SpeakerKit d'Argmax avec les modèles
   pyannote segmentation-3.0, WeSpeaker ResNet34 et pyannote
   community-1, convertis en Core ML par Argmax) s'exécute dans
   l'application via Core ML et est désactivable. La détection
   d'activité vocale (Silero VAD 5.1.2 dans whisper.cpp) n'est utilisée
   que si la séparation des locuteurs est désactivée ; sinon, c'est la
   séparation des locuteurs qui découpe les blocs. Tous les modèles
   sont contenus dans le paquet de l'application ; elle ne télécharge
   ni modèles ni composants de programme. D'autres modèles whisper.cpp
   ne peuvent être ajoutés qu'à la main, dans le dossier « Modelle » de
   la bibliothèque. Les modèles n'apprennent rien des enregistrements.
   L'application ne résume rien et ne reformule rien ; la
   reconnaissance vocale est un modèle d'IA et peut poser des mots qui
   n'ont pas été dits, d'où la vérification de la transcription en
   regard de l'enregistrement.
3. **Stockage.** Pour chaque transcription, un sous-dossier est créé
   dans le dossier de bibliothèque choisi `[chemin]`, contenant
   `transkript.json` (texte, locuteurs, mémos, journal, indications
   Zotero), une copie de l'enregistrement (pour une vidéo aussi le
   fichier vidéo inchangé) et `wellenform.json`. `ausgang.json`
   conserve l'état tel que la machine ou un fichier importé l'a livré ;
   `history/` conserve les 30 derniers états. **Tous deux contiennent
   le texte d'avant une pseudonymisation.** Les réglages et le journal
   de l'application se trouvent dans le conteneur de l'application du
   compte utilisateur. Le journal de la transcription consigne un
   identifiant de l'installation et, en option, une adresse e-mail de
   la personne qui révise.
4. **Réseau.** Le logiciel ne transmet ni enregistrements, ni textes,
   ni données d'utilisation : ni compte, ni télémétrie, ni vérification
   des mises à jour, ni rapports de plantage propres, ni téléchargement
   de modèles. Il n'y a ni service interne, ni serveur, ni port ouvert.
   L'autorisation réseau de macOS n'est activée que parce que la vue
   web intégrée l'exige ; un pare-feu ou `nettop` montre qu'aucune
   connexion ne s'établit. Les rapports de plantage du système macOS
   relèvent de ses réglages système, non du logiciel.
5. **Sortie.** Les fichiers d'export sont écrits là où
   l'utilisateur·rice les enregistre. Tous les formats de texte (VTT,
   CSV, TXT, Markdown, Word) contiennent texte, noms des locuteurs et
   repères temporels ; CSV, Markdown et Word en plus les mémos ;
   Markdown et Word, en cas de lien Zotero, un en-tête avec titre,
   date, clé de citation et les personnes dont les rôles ont été
   choisis. **REFI-QDA (`.qdpx.zip`) contient texte, mémos et
   enregistrement audio, donc la voix, et sur demande le fichier
   vidéo ; le dossier enrich (`.enrich`) contient texte, enregistrement
   audio en MP3 (via LAME), journal avec identifiant de l'installation
   et adresse e-mail, et indications Zotero, pas de mémos.** Les
   transmettre, c'est transmettre l'enregistrement. Avec l'autorisation
   Zotero, l'application lit la base locale `zotero.sqlite` en lecture
   seule, uniquement sur demande. Pour un enregistrement vidéo, le
   fichier vidéo est conservé tel quel dans le dossier de la
   transcription (les visages sont des données personnelles,
   biométriques si identifiables).

## 5. Lieu du traitement

Exclusivement sur l'appareil `[appareil, lieu]`, dans la session de la
personne connectée. Il n'y a ni serveur, ni port ouvert, ni service
cloud, ni compte utilisateur.

## 6. Destinataires, sous-traitants, transferts vers des pays tiers

Aucun. Comme aucune donnée n'est transmise, il n'y a ni destinataire,
ni sous-traitant, ni transfert vers un pays tiers. Les données ne
quittent l'appareil que si le responsable du traitement transmet
lui-même des fichiers d'export `[à …, par …]`.

## 7. Durée de conservation et suppression

Conservation des enregistrements et transcriptions : `[durée, base]`.
Supprimer dans l'application déplace une entrée vers un dossier
corbeille à l'intérieur de la bibliothèque (`_papierkorb`) ; elle n'est
définitivement effacée qu'en vidant ce dossier dans le Finder `[par
qui, quand]`. `ausgang.json` et les états de `history/` se trouvent
dans le dossier de la transcription concernée et sont supprimés avec
elle. Les sauvegardes de l'appareil
`[Time Machine, …]` relèvent de la règle de suppression du responsable.

## 8. Mesures techniques et organisationnelles

À la charge du responsable du traitement, le logiciel n'apportant
lui-même aucun contrôle d'accès :

- Chiffrement du disque, p. ex. FileVault : `[actif depuis …]`
- Protection d'accès à l'appareil (connexion, verrouillage d'écran) :
  `[…]`
- Pseudonymisation avant toute transmission — dans l'éditeur de
  l'application, les locuteurs peuvent être renommés et les noms dans le
  texte remplacés par rechercher-remplacer ; la décision de ce qu'il faut
  remplacer revient à la personne qui édite : `[procédure,
  responsabilité]`
- Règle de sauvegarde : `[…]`
- Règle de transmission des fichiers d'export, en particulier ceux
  contenant l'audio : `[…]`

## 9. Base légale et information des personnes concernées

`[consentement / intérêt légitime / privilège de recherche selon … ;
lettre d'information du …]`. Le logiciel n'y contribue en rien.

## 10. Vérifiabilité

Les affirmations de la section 4 peuvent être vérifiées dans le code
source : le shell `frontend/src-tauri/src/lib.rs` ne démarre aucun
serveur et n'ouvre aucun port ; les autorisations de la sandbox
figurent dans `frontend/src-tauri/entitlements.plist`. Le dépôt
contient toute la chaîne de construction jusqu'au paquet d'installation
signé ; qui ne fait pas confiance au binaire distribué peut le compiler.

---

Source de ce texte : <https://github.com/bias-city/ResearchTranscript>
(dossier `site/docs`). Il est publié sous CC BY 4.0 : utilisation et
adaptation libres, y compris commerciales, à condition de citer B/IAS
et d'indiquer les modifications.
