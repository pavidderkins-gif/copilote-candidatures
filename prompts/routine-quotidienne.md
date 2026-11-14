# Routine quotidienne — recherche, notation, dashboard, email (v3, 14/11/2026, remplace la v2)

Lancée chaque matin à 6 h 58 (heure de Paris). Objectif : trouver les nouvelles offres qui
collent au profil de David, **les lire en entier**, les noter, alimenter son dashboard, préparer
les dossiers qu'il a demandés et lui envoyer un email **court et clair** : il doit gagner du
temps, pas en perdre. Chercher partout, ne montrer que le meilleur.

**Dashboard :** https://claude.ai/artifact/QngVuEMvQQTe5yhy1Pqgsg — sa base de données se lit
et s'écrit avec l'outil `ArtifactData` (`url` ci-dessus). Collections : `offres/<dedup_hash>`,
`suivi/<dedup_hash>` (écrit par David : son étape et ses notes), `dossiers/<dedup_hash>`,
`rapports/<AAAA-MM-JJ>`, `reglages/general`.

**Interdits absolus :** ne jamais postuler ; jamais rien préparer ni envoyer pour une offre
du groupe LVMH (David postule en interne) ; ne jamais contacter un recruteur ; ne jamais se
connecter à LinkedIn ou Indeed (lire seulement les alertes reçues par email) ; ne jamais
inventer une offre, une date, un lien ou un fait du profil ; ne jamais écrire dans
`suivi/` sauf pour passer une offre de « dossier_demande » à « dossier_pret ».

## 0. Préparation

1. `git pull` dans `copilote-candidatures`, puis **se placer sur la branche `main`** (c'est la
   seule branche de travail, celle que voit David et la session de maintenance) :
   `git fetch origin main && git checkout main && git pull --ff-only origin main` (si `main`
   n'existe pas en local : `git checkout -b main origin/main`). Si ce fichier a changé avec ce
   pull, le relire avant de continuer. Tous les commits sont poussés sur `main`.
2. Lire `profil/profil-maitre.md`, `profil/perimetre.yaml`, `profil/regles.yaml`, `prompts/scoring.md`.
3. Lire les réglages de David : `ArtifactData get reglages/general` (seuil, passe_droit,
   plafond_jour, cibles). Ils remplacent les valeurs de `perimetre.yaml`.
4. Lire `suivi` (`ArtifactData list suivi`, limit 1000) : noter les offres en
   `dossier_demande` (étape 6) et celles en `postulee` depuis 7 jours ou plus (relances).
5. Date du jour (heure de Paris) : `AAAA-MM-JJ`.

## Règles d'or (décisions de David du 13 et du 14/11/2026)

1. **Seulement du neuf** : publié depuis le passage précédent (48 h ; 72 h le lundi).
   `N` = 2 (3 le lundi) dans les commandes ci-dessous.
2. **Seulement des offres lues en entier** : chaque offre passe par `scripts/qualite.py` sur son
   texte complet. Sans texte complet, elle n'est jamais montrée.
3. **Tout ce qui peut être vérifié l'est avant l'email** (langue exigée, nationalité, expérience,
   date, lien). Jamais de « à vérifier » que le texte de l'offre permet de trancher.
4. **Lien direct de l'entreprise** : site carrières / outil de recrutement de l'entreprise ;
   à défaut l'annonce jobup / jobs.ch / HelloWork ; pour un VIE, la page de l'entreprise, sinon
   Business France, sinon la page iagora. Jamais une page de résultats ni un agrégateur
   (Indeed, Glassdoor, Jobleads…) pour un CDI.
5. **Email court** : l'essentiel de chaque offre en 3 lignes (le poste, pour toi, à savoir).

## 1. Collecte (lancer les trois scripts en parallèle, en arrière-plan)

```bash
python3 scripts/jobup.py --jours N --complet > /tmp/c_jobup.jsonl 2> /tmp/c_jobup.log     # Suisse romande + Zurich + SIG (~3 min)
python3 scripts/workday.py --jours N > /tmp/c_workday.jsonl 2> /tmp/c_workday.log         # sites carrières : Suisse, Australie, France, VIE (~5-10 min)
python3 scripts/vie.py --jours N > /tmp/c_vie.jsonl 2> /tmp/c_vie.log                    # tous les VIE finance / supply chain / data / achats (~1 min)
```

Chaque ligne a déjà `texte` (description complète), `controles` et `exclusion`.
Pendant ce temps :

**a. Alertes Gmail** des N derniers jours :
`newer_than:Nd from:(linkedin.com OR businessfrance.fr OR sig-ge.ch OR jobs.ch OR jobup.ch OR seek.com.au OR welcometothejungle.com OR apec.fr OR jobteaser.com)`
(Alertes créées par David le 15/11 : VIE Business France, SIG, LinkedIn. Si une alerte arrive
d'un autre expéditeur d'emploi, l'ajouter à cette requête.) Lire chaque email d'alerte en
entier (`get_thread`) : il liste plusieurs offres. Pour chaque offre : retrouver le lien de
l'entreprise (une alerte LinkedIn donne l'entreprise et l'intitulé : chercher l'offre sur son
site carrières ; ne jamais ouvrir LinkedIn), puis la lire et la contrôler :
`printf '%s\n' <lien1> <lien2> … | python3 scripts/lire_offre.py | python3 scripts/qualite.py >> /tmp/c_autres.jsonl`

**b. Paris et Lyon** : HelloWork filtré CDI et dernière semaine
(`https://www.hellowork.com/fr-fr/emploi/recherche.html?k=<terme>&l=<ville>&c=CDI&d=w`, termes :
data analyst, business analyst, analyste financier, contrôleur de gestion, FP&A, supply chain
analyst), puis chaque offre lue et contrôlée de la même façon (`>> /tmp/c_autres.jsonl`).

**c. Recherche web** (WebSearch `extended`, en parallèle) pour ce que les scripts ne couvrent
pas. Chaque piste doit être retrouvée sur le site de l'entreprise puis lue avec `lire_offre.py`
et contrôlée avec `qualite.py` ; sinon elle est abandonnée.

| # | Requête type | Pourquoi |
|---|---|---|
| 1 | `"Data Analyst" OR "Business Analyst" OR "Financial Analyst" junior Genève OR Lausanne <mois> <année>` | Suisse romande, zone n°1 |
| 2 | `graduate OR trainee programme <année+1> finance OR data Genève OR Zurich` (UBS, Pictet, Lombard Odier, Nestlé, PMI, JTI, dsm-firmenich, Givaudan, SGS, Rolex) | Programmes jeunes diplômés |
| 3 | `"Services Industriels de Genève" OR SIG "premier emploi" analyste OR finance OR data` | SIG, cible de David |
| 4 | `graduate program <année+1> analyst Sydney OR Melbourne OR Brisbane finance OR data` (Macquarie, ANZ, Westpac, Deloitte, KPMG, EY, PwC, Suncorp, Canva, Atlassian) | Australie, seulement le très bon |
| 5 | `"junior" "data analyst" OR "financial analyst" OR "business analyst" Sydney OR Melbourne OR Brisbane` | Australie, premiers postes |
| 6 | `VIE <année+1> "Financial Analyst" OR "Contrôleur de gestion" OR "Data Analyst" OR "Supply Chain" Londres OR "New York" OR Singapour OR Sydney OR Montréal OR Dublin` | VIE anglophones |
| 7 | `offre CDI "Data Analyst junior" OR "FP&A" OR "Contrôleur de gestion junior" Paris <mois> <année>` | Paris |
| 8 | `<entreprise cible> careers junior analyst` pour 5 entreprises de `reglages.cibles`, en tournant | Entreprises cibles |
| 9 | `site:lvmh.com join-us our-job-offers analyst` | Groupe LVMH (rubrique interne) |
| 10 | `CERN junior OR graduate finance OR data OR supply chain Geneva` | CERN |

Tout rassembler dans `/tmp/candidats.jsonl` (une offre par ligne, avec `texte`, `controles`,
`exclusion`, `zone`).

## 2. Contrôle, fraîcheur, déduplication

1. Mettre de côté les offres dont `exclusion` n'est pas vide (les compter pour l'email :
   « N écartées »). Relire la preuve citée seulement si elle paraît absurde.
2. Écarter les offres publiées avant le passage précédent.
3. Dédupliquer : `python3 scripts/offres.py filtrer < /tmp/candidats_ok.jsonl > /tmp/nouvelles.jsonl`

## 3. Notation et catégorie

Appliquer `prompts/scoring.md` (v2) à chaque nouvelle offre, en lisant son texte complet
(réglages de David en priorité). Remplir `categorie` (`postuler`, `vie`, `australie`, `lvmh`,
`a_surveiller`), `en_bref`, `pour_toi`, `a_savoir`, `contrat`, `duree`, `salaire` (si l'offre
le donne), `points_forts`, `ecarts`, `motif`, `rapport: "<AAAA-MM-JJ>"`, `date_collecte`.
Statuts : `propose` (catégories postuler / vie / australie), `a_surveiller`, `archive`, `exclu`.
Offres LVMH : `groupe_lvmh: true`, `canal: "interne_lvmh"`.

## 3 bis. Liens

1. Pour chaque offre retenue (postuler, vie, australie), trouver le lien de l'entreprise si la
   source n'en est pas un : `python3 scripts/jobup.py --detail <id>` (lien externe d'une annonce
   jobup), recherche ciblée `<entreprise> "<intitulé>"`, flux de l'outil de recrutement. Pour
   un VIE iagora : chercher l'offre chez l'entreprise (Workday, site carrières) ; si
   l'entreprise n'est pas indiquée, garder la page iagora avec `lien: "iagora (postuler via
   Business France)"`.
2. `lien_verifie` : `ok` (en ligne, intitulé retrouvé), `protege` (site officiel qui bloque les
   robots : accepté), `retire` (404, page d'erreur, absente du flux → `exclu`),
   `non_verifiable` (agrégateur → pas de CDI dans l'email).
3. Chaque matin, revérifier aussi les offres actives et suivies :
   `python3 scripts/verifier_liens.py /tmp/db/offres /tmp/db/suivi > /tmp/liens.jsonl`
   (exporter `offres` et `suivi` avec `ArtifactData list` + `out_dir` ; les fichiers exportés
   n'ont pas la version : la reprendre dans la liste renvoyée pour écrire avec `if_version`).
   Une offre `retire` passe en `exclu` (« offre retirée ») ; une offre suivie retirée va dans
   « À faire » de l'email.

## 4. Enregistrement

```bash
python3 scripts/offres.py ajouter < /tmp/notees.jsonl
```

Puis écrire chaque offre notée dans le dashboard (sans les champs `texte` et `controles`,
trop volumineux : garder `en_bref`, `pour_toi`, `a_savoir`, `categorie`) : un fichier JSON par offre, et
`ArtifactData batch` (50 écritures maximum par lot, `op: "set"`, `collection: "offres"`,
`doc_id: <dedup_hash>`, `file_path`). Ne jamais réécrire une offre déjà présente.

## 5. Rapport

- `rapports/AAAA-MM-JJ.md` dans le dépôt : le même contenu que l'email (texte), puis la liste
  des offres écartées avec leur motif (une ligne chacune), pour garder la trace.
- Document `rapports/<AAAA-MM-JJ>` dans le dashboard : `date`, `lien` (GitHub), `nb_trouvees`,
  `nb_proposees`, `nb_exclues`, `nb_vie`, `questions` (infos manquantes pour David).

## 6. Dossiers demandés depuis le dashboard

Pour chaque offre en `dossier_demande` (sauf LVMH, jamais) : suivre
`prompts/generation-dossier.md`, écrire `dossiers/<dedup_hash>`, puis passer
`suivi/<dedup_hash>` à `etape: "dossier_pret"` avec `ArtifactData update` (pinné sur la
`version` lue à l'étape 0, sans toucher aux autres champs).

**Dossiers incomplets** : si Canva répond, compléter aussi chaque dossier marqué
`cv_a_generer: true` (CV Canva ciblé et PDF selon `prompts/generation-dossier.md` § 1 à 2 bis,
puis `cv_a_generer` supprimé) et chaque dossier sans `portfolio_pdf_url` (§ 2 ter). Écrire avec
`ArtifactData update` pinné sur la version lue, et les signaler dans l'email du matin.

## 6 bis. Relances (J+7 et J+14)

Pour chaque offre en `postulee` ou `relance` depuis 7 jours (puis 14 jours) sans réponse :
écrire un message de relance court et poli dans la langue de l'offre (rappel du poste, une
phrase de valeur ajoutée, question sur la suite ; « Respectueusement » ou « Kind regards »)
dans le champ `relance` de `dossiers/<dedup_hash>` (créer le document s'il n'existe pas). Si
un email de contact est connu (notes de David ou offre), créer un **brouillon** Gmail. Le
signaler dans l'email du matin. Ne jamais l'envoyer soi-même.

## 6 ter. Entretiens

Pour chaque offre passée en `entretien` sans `preparation_entretien` : suivre
`prompts/preparation-entretien.md` et écrire le résultat dans le champ
`preparation_entretien` de `dossiers/<dedup_hash>`. Si les notes de David donnent une date
et une heure d'entretien, créer l'événement dans Google Calendar (titre « Entretien –
<entreprise> – <poste> », lien de l'offre en description) s'il n'existe pas déjà.

## 6 quater. Réponses des recruteurs

Chercher dans Gmail les réponses des 3 derniers jours aux candidatures envoyées (nom de
l'entreprise dans l'expéditeur ou l'objet). Les signaler dans l'email du matin et le rapport
(accusé de réception, refus, invitation à un entretien). Ne pas changer l'étape soi-même :
David la met à jour dans le tableau de bord.

## 7. Publication

```bash
git add rapports/ donnees/ dossiers/ && git commit -m "Rapport du AAAA-MM-JJ" && git push origin main
```

En cas de refus du push (commit arrivé entre-temps) : `git pull --rebase origin main`, puis
`git push origin main`.

## 8. Envoi à David (email court, toujours le même format)

1. Écrire `/tmp/selection.json` (format décrit en tête de `scripts/email_rapport.py`) :
   `date`, `stats` (`lues` = offres lues en entier, `exclues`, `vie_trouves` = VIE nouveaux
   avant notation), `offres` (catégories postuler, vie, australie, lvmh ; avec `en_bref`,
   `pour_toi`, `a_savoir`, `contrat`, `salaire`, `url`, `lien` = nom du site, par exemple
   « site Airbus », `date_publication`, `dossier_pret`), `a_faire` (relances dues, offres
   suivies retirées, réponses de recruteurs, dossiers prêts : une ligne chacun).
2. `python3 scripts/email_rapport.py /tmp/selection.json > /tmp/email.json`
3. Gmail `send_message` à l'adresse Gmail de David : `subject` = `objet`, `body` = `texte`,
   `htmlBody` = `html` (sans rien ajouter). Si l'envoi échoue, créer un brouillon et le
   signaler dans le rapport.

Style des trois lignes (20 mots maximum chacune, en français, sans jargon) :
- **Le poste** : le travail concret (« Contrôle de gestion d'une filiale Airbus : clôtures,
  budget, tableaux Power BI, 24 mois »), pas la présentation de l'entreprise.
- **Pour toi** : le lien avec une expérience précise de David (« Tes outils de trésorerie
  Cogeco et tes dashboards Dior »).
- **À savoir** : la vraie contrainte tirée du texte (« 2-3 ans demandés », « démarrage
  immédiat », « allemand apprécié, pas exigé », « droit de travail australien exigé »), ou rien.

**Si les connecteurs Gmail ou Canva ne répondent pas** (outils absents de la session) : ne pas
s'arrêter. Faire tout le reste (sourcing, vérification des liens, notation, tableau de bord,
rapport GitHub) ; pour les dossiers demandés, préparer la lettre, le message et le pitch, et
noter dans `questions` « CV Canva à générer dès que Canva sera reconnecté ». Prévenir David
par notification (PushNotification) avec le nombre d'offres et le lien du tableau de bord, et
écrire en tête du rapport que les connecteurs sont à vérifier sur
https://claude.ai/customize/connectors. Terminer par un résumé
de 3 lignes dans la conversation.
