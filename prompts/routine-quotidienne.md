# Routine quotidienne — recherche, notation, dashboard, rapport (v2)

Lancée chaque matin à 6 h 58 (heure de Paris). Objectif : trouver les nouvelles offres qui
collent au profil de David, les noter, alimenter son dashboard, préparer les dossiers qu'il a
demandés et lui envoyer un récapitulatif lisible en 2 minutes.

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

1. `git pull` dans `copilote-candidatures`.
2. Lire `profil/profil-maitre.md`, `profil/perimetre.yaml`, `profil/regles.yaml`, `prompts/scoring.md`.
3. Lire les réglages de David : `ArtifactData get reglages/general` (seuil, passe_droit,
   plafond_jour, cibles). Ils remplacent les valeurs de `perimetre.yaml`.
4. Lire `suivi` (`ArtifactData list suivi`, limit 1000) : noter les offres en
   `dossier_demande` (étape 6) et celles en `postulee` depuis 7 jours ou plus (relances).
5. Date du jour (heure de Paris) : `AAAA-MM-JJ`.

## Règles d'or (décisions de David du 13/11/2026)

1. **Seulement du neuf** : le rapport ne montre que les offres publiées depuis le passage
   précédent (48 heures, 72 heures le lundi). Une offre plus ancienne a déjà été vue.
2. **Seulement des liens vérifiés** : aucune offre n'entre dans la sélection sans lien
   vérifié (étape 3 bis). Lien à donner, dans l'ordre : l'offre sur le site carrières de
   l'entreprise, sinon l'annonce sur le site d'emploi. Jamais une page de résultats ni un
   agrégateur (Indeed, Glassdoor, Jobleads, iagora…).

## 1. Sourcing (viser 60 à 100 offres candidates)

**Sources fiables d'abord** (date de publication réelle et lien direct) :
- Suisse : `python3 scripts/jobup.py --jours 2 > /tmp/jobup.jsonl` (jobup.ch et jobs.ch,
  recherches du périmètre). `--jours 3` le lundi.
- Paris et Lyon : pages de résultats HelloWork filtrées CDI et « dernière semaine »
  (`https://www.hellowork.com/fr-fr/emploi/recherche.html?k=<terme>&l=<ville>&c=CDI&d=w`),
  puis la page de chaque offre (`/fr-fr/emplois/<id>.html`).
- Entreprises cibles : leurs flux publics quand ils existent (Workable
  `apply.workable.com/api/v1/widget/accounts/<compte>`, Greenhouse
  `boards-api.greenhouse.io/v1/boards/<compte>/jobs`, Lever `api.lever.co/v0/postings/<compte>`,
  SmartRecruiters `api.smartrecruiters.com/v1/companies/<compte>/postings` — CERN : `CERN`,
  Workday, SuccessFactors).
- La recherche web (1c) sert seulement à découvrir des pistes : chaque piste doit ensuite
  être retrouvée sur le site de l'entreprise ou sur un site d'emploi lisible.

Toujours avec curl simple, sans modifier l'en-tête, avec une pause entre les requêtes.

Tester d'abord si la lecture de pages fonctionne (`WebFetch` sur une page de résultats
jobup.ch). Si oui, lire les pages de résultats triées par date des sites listés en 1b ; sinon,
s'appuyer sur la recherche web (1c) et marquer les notes « provisoires ».

**a. Alertes Gmail** des 2 derniers jours :
`newer_than:2d from:(jobalerts-noreply@linkedin.com OR jobs-noreply@linkedin.com OR apec.fr OR welcometothejungle.com OR jobteaser.com OR jobs.ch OR jobup.ch OR businessfrance.fr)`

**b. Sites d'emploi** (si la lecture de pages fonctionne) : jobup.ch, jobs.ch, datacareer.ch,
welcometothejungle.com, apec.fr, candidat.francetravail.fr, hellowork.com,
mon-vie-via.businessfrance.fr, lvmh.com/fr/nous-rejoindre.

**c. Plan de recherche web** (WebSearch, mode `extended`, toutes en parallèle) — il a
donné les meilleures offres du 13/11 :

| # | Requête type | Pourquoi |
|---|---|---|
| 1 | `"Data Analyst" OR "Business Analyst" junior Genève OR Lausanne CDI <mois> <année>` | Suisse romande, zone n°1 |
| 2 | `junior "Data Analyst" OR "BI Analyst" OR "FP&A" Zurich OR Basel English no German` | Suisse anglophone |
| 3 | `"Supply Chain Analyst" OR "Demand Planner" junior Genève OR Vaud OR Neuchâtel` | Supply chain en Suisse |
| 4 | `graduate programme <année+1> finance OR data Zurich OR Genève` (Swiss Re, UBS, Julius Baer, Pictet, Lombard Odier) | Programmes graduate : idéal premier emploi |
| 5 | `offre CDI "Data Analyst junior" OR "Business Data Analyst" Paris <mois> <année>` | Paris data |
| 6 | `"FP&A Analyst" OR "Analyste FP&A" OR "Contrôleur de gestion junior" CDI Paris <mois>` | Paris finance |
| 7 | `"Data Analyst" OR "Contrôleur de gestion junior" OR "Supply Chain Analyst" CDI Lyon <mois>` | Lyon |
| 8 | `"Chief of Staff" OR "Business Operations" junior Paris startup CDI` | Axe startup |
| 9 | `VIE <année+1> "Data Analyst" OR "Financial Analyst" OR "Business Analyst" Londres OR "New York" OR Singapour OR Sydney OR Montréal OR Dublin` | VIE anglophones |
| 10 | `VIE "Supply Chain" OR "Demand Planning" analyst <année+1>` | VIE supply chain |
| 11 | `<entreprise cible> careers junior analyst` pour 5 entreprises de `reglages.cibles`, en tournant chaque jour | Entreprises cibles |
| 12 | `site:lvmh.com join-us our-job-offers analyst` | Groupe LVMH (rubrique interne) |
| 13 | `BNP Paribas OR "Société Générale" OR Bpifrance CDI junior "Data Analyst" OR "Business Analyst"` | Banques |
| 14 | `junior "Data Analyst" OR "Business Analyst" Mistral AI OR Qonto OR Pennylane OR Finary OR Photoroom` | IA et fintech |
| 15 | `CERN junior OR graduate supply chain OR data Geneva` | Le CERN recrute des juniors avec des délais courts |

Pour chaque offre prometteuse, faire une recherche ciblée (`<entreprise> "<intitulé>"`) pour
retrouver le lien direct de l'annonce (site carrières, Workable, Greenhouse, Lever…) et sa date.
Un lien vers une page de résultats est accepté seulement avec la mention « offre exacte à
retrouver ».

Écrire chaque offre candidate dans `/tmp/candidates.jsonl`.

## 2 bis. Fraîcheur

Écarter toute offre dont `date_publication` est antérieure au dernier passage (48 h ; 72 h le
lundi). Sans date fiable : l'offre ne va pas dans la sélection, au mieux « à surveiller ».

## 2. Déduplication

```bash
python3 scripts/offres.py filtrer < /tmp/candidates.jsonl > /tmp/nouvelles.jsonl
```

## 3. Notation

Appliquer `prompts/scoring.md` à chaque nouvelle offre (réglages de David en priorité).
Ajouter `points_forts` (2 ou 3, concrets, reliés au profil maître), `ecarts` (avec la façon de
compenser), `canal`, `date_publication` si connue, `motif` (remarque ou motif d'exclusion),
`rapport: "<AAAA-MM-JJ>"`, `date_collecte`. Statuts : `propose`, `a_surveiller`, `archive`, `exclu`.

Sélection du jour (hors LVMH) : toutes les offres ≥ passe_droit, puis les meilleures au-dessus
du seuil jusqu'à plafond_jour. Les autres au-dessus du seuil passent en `a_surveiller`.
Offres LVMH : `groupe_lvmh: true`, `canal: "interne_lvmh"`, hors sélection.

## 3 bis. Vérification des liens (obligatoire avant le rapport)

Pour chaque offre `propose` ou `a_surveiller` :
1. Chercher le lien de candidature sur le site de l'entreprise (`python3 scripts/jobup.py
   --detail <id>` pour jobup ; flux ATS de l'entreprise ; recherche ciblée). Suivre les
   redirections (`curl -sL -o /dev/null -w "%{http_code} %{url_effective}"`).
2. Statut du lien (`lien_verifie`) :
   - `ok` : code 200 et l'offre est bien présente (titre retrouvé dans la page ou dans le
     flux officiel de l'entreprise) ;
   - `protege` : site officiel qui bloque la vérification automatique (403) : accepté
     seulement pour une page officielle de l'entreprise, avec la mention « ouvre pour vérifier » ;
   - `retire` : 404, 410, redirection vers une liste ou une page d'erreur, ou offre absente du
     flux officiel → statut `exclu`, motif « offre retirée » ;
   - `non_verifiable` : agrégateur ou page de résultats → statut `archive`.
3. Enregistrer `lien_verifie` et `lien_verifie_le` (AAAA-MM-JJ) dans l'offre.
4. Revérifier aussi, chaque matin, les liens des offres que David suit (`interessante`,
   `dossier_demande`, `dossier_pret`) : si l'une est retirée, le dire en tête de l'email.

## 4. Enregistrement

```bash
python3 scripts/offres.py ajouter < /tmp/notees.jsonl
```

Puis écrire chaque offre notée dans le dashboard : un fichier JSON par offre, et
`ArtifactData batch` (50 écritures maximum par lot, `op: "set"`, `collection: "offres"`,
`doc_id: <dedup_hash>`, `file_path`). Ne jamais réécrire une offre déjà présente.

## 5. Rapport

- `rapports/AAAA-MM-JJ.md` dans le dépôt (format du rapport du 13/11/2026).
- Document `rapports/<AAAA-MM-JJ>` dans le dashboard : `date`, `lien` (GitHub), `nb_trouvees`,
  `nb_proposees`, `nb_exclues`, `questions` (infos manquantes pour David), `avertissement`
  (si les notes sont provisoires).

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
git add rapports/ donnees/ && git commit -m "Rapport du AAAA-MM-JJ" && git push
```

## 8. Envoi à David

Email (Gmail `send_message`) à l'adresse Gmail de David, sans pièce jointe :
- Objet : `Copilote · N offres le JJ/MM` (ou `Copilote · rien de nouveau le JJ/MM`).
- Corps en texte simple : offres sélectionnées (poste, entreprise, lieu, note, lien), offres
  LVMH sous « Groupe LVMH (candidature interne) », dossiers prêts à relire, relances à faire,
  questions, puis les liens vers le dashboard et le rapport GitHub. Signé « Respectueusement ».

Si l'envoi échoue, créer un brouillon et le signaler dans le rapport.

**Si les connecteurs Gmail ou Canva ne répondent pas** (outils absents de la session) : ne pas
s'arrêter. Faire tout le reste (sourcing, vérification des liens, notation, tableau de bord,
rapport GitHub) ; pour les dossiers demandés, préparer la lettre, le message et le pitch, et
noter dans `questions` « CV Canva à générer dès que Canva sera reconnecté ». Prévenir David
par notification (PushNotification) avec le nombre d'offres et le lien du tableau de bord, et
écrire en tête du rapport que les connecteurs sont à vérifier sur
https://claude.ai/customize/connectors. Terminer par un résumé
de 3 lignes dans la conversation.
