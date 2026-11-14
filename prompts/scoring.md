# Notation d'une offre — version v2 (14/11/2026)

> Rédigée d'après le cahier des charges (le « mode B du coach » n'a pas été fourni).
> La version est enregistrée avec chaque note (`version_prompt: scoring-v2`).

Entrées : le **texte complet** de l'offre (lu avec `scripts/lire_offre.py` ou un collecteur),
le résultat de `scripts/qualite.py`, `profil/profil-maitre.md`, `profil/perimetre.yaml`.

**On ne note jamais une offre qu'on n'a pas lue en entier.** Si le texte complet n'a pas pu
être lu (moins de 400 caractères), l'offre n'est ni notée ni montrée à David.
**Tout ce que le texte permet de vérifier est vérifié avant de montrer l'offre** : on ne
renvoie jamais à David une vérification du type « vérifier que l'allemand n'est pas exigé »
(erreur du 13/11 avec un VIE BNP Paribas en Allemagne : l'offre disait « allemand courant »).

## 1. Filtres d'exclusion (avant toute note)

Si l'un de ces cas s'applique, l'offre est **exclue** : statut `exclu`, motif noté, pas de note.

- `exclusion` non vide dans le résultat de `scripts/qualite.py` : langue autre que français ou
  anglais exigée (allemand, néerlandais, espagnol, italien…), offre rédigée en allemand,
  nationalité / résidence permanente / habilitation étrangère exigée, stage ou alternance,
  poste senior ou de management, 5 ans d'expérience ou plus. Relire la phrase citée en preuve :
  si c'est un faux positif évident (« German market »), le noter dans `motif` et continuer.
- Langue « un plus » (`langues_un_plus`) : pas d'exclusion, mais le dire dans `a_savoir`.
- Poste de conseil ou de placement chez un client : cabinet de conseil, ESN/SSII, intitulé
  contenant « consultant » ou « consulting ». (Un poste interne de finance ou de contrôle
  de gestion dans une ESN, par exemple en VIE, n'est pas du conseil : il est noté.)
- Ingénieur d'affaires, ingénieur commercial, business developer, key account.
- Expérience exigée supérieure à `exclusions.experience_max_annees` (4 ans).
- Zone hors périmètre : ni Suisse, ni Paris/Île-de-France, ni Lyon, ni VIE, ni Australie
  (Sydney, Melbourne ou Brisbane seulement).
- VIE en Chine, au Japon ou en Corée.
- Site isolé, loin d'une ville.
- Stage, alternance ou poste étudiant (David cherche un CDI ou un VIE à partir de février 2027).
- Offre expirée, retirée (lien mort) ou publiée avant le passage précédent (48 h ; 72 h le lundi).

## 2. Note brute sur 10

| Critère | Points | Ce qui donne le maximum |
|---|---|---|
| Missions | 0 à 3 | Analyse de données pour aider à décider, ou analyse financière (priorité n°1) : dashboards, modélisation, prévision, reporting de direction |
| Compétences | 0 à 2 | La plupart des compétences demandées sont dans le profil : Power BI/DAX, SQL, Python, Excel/VBA, SAP, GCP |
| Séniorité | 0 à 2 | Jeune diplômé ou 0 à 2 ans ; 1 point pour 2 à 4 ans |
| Zone | 0 à 1 | Suisse 1 ; Australie (Sydney, Melbourne, Brisbane) 0,75 ; Paris 0,75 ; VIE pays anglophone 0,75 ; Lyon 0,5 ; autre VIE 0,5 |
| Signaux implicites | 0 à 1,5 | Autonomie, projet de bout en bout, lien métier-technique, dimension humaine, apprentissage rapide, environnement international |
| Contrat et date | 0 à 0,5 | CDI ou VIE, démarrage compatible avec février 2027 |

## 3. Bonus (note finale plafonnée à 10)

- +1 : entreprise de `entreprises.cibles` (dont SIG, Services Industriels de Genève)
- +1 : groupe LVMH ou une de ses Maisons (`entreprises.groupe_lvmh_mots_cles`)
- +0,5 : banque
- +0,5 : IA (entreprise d'IA ou poste centré sur l'IA)

### Groupe LVMH

Une offre du groupe LVMH ou d'une de ses Maisons est notée normalement (bonus compris), mais
elle reçoit `"groupe_lvmh": true` et `"canal": "interne_lvmh"`. Elle n'entre pas dans les 5
dossiers du jour : elle va dans une rubrique à part du rapport. **L'outil ne postule jamais et
ne prépare aucun envoi pour ces offres : David postule lui-même en interne.**

## 4. Où va l'offre (catégorie de l'email)

| Catégorie | Règle |
|---|---|
| `postuler` | CDI / CDD en Suisse, à Paris ou à Lyon : toutes les offres ≥ `passe_droit` (8), puis les meilleures ≥ `seuil` (6) jusqu'à `plafond_jour` (5) |
| `vie` | **Tous** les VIE du périmètre (finance, contrôle de gestion, data / BI, business analysis, supply chain, achats) avec une note ≥ 5, « au cas où » (demande de David du 14/11) ; hors Chine, Japon, Corée |
| `australie` | Sydney, Melbourne ou Brisbane, note ≥ 8 seulement (« que des très bonnes offres »). David n'a pas encore de droit de travail (visa post-études 485 probable) : si l'offre exige « full working rights », `a_savoir` = « Droit de travail exigé : il te faudrait le visa post-études (485) » ; si elle propose un sponsoring de visa, le dire (+0,5 en signaux implicites) |
| `lvmh` | Groupe LVMH : signalé, jamais de dossier (voir plus haut) |
| `a_surveiller` | Au-dessus du seuil mais hors sélection : tableau de bord seulement, pas dans l'email |

## 4 bis. Recommandation

- Note finale ≥ `scoring.seuil` (6) sans écart bloquant → **postuler**
- Note finale ≥ seuil avec un écart à compenser (compétence manquante, séniorité limite) → **postuler en compensant**, en disant comment compenser
- Note finale < seuil → **passer**

## 5. Sortie attendue (une ligne JSON par offre)

```json
{"entreprise": "...", "intitule": "...", "lieu": "...", "pays": "...", "contrat": "CDI|VIE|CDD|autre",
 "categorie": "postuler|vie|australie|lvmh|a_surveiller", "duree": "24 mois", "salaire": "",
 "en_bref": "ce que fait le poste, 20 mots maximum", "pour_toi": "pourquoi ça colle, 20 mots maximum",
 "a_savoir": "la vraie contrainte tirée du texte, 20 mots maximum (ou vide)",
 "langue": "fr|en", "axe": "data_bi|finance|supply_chain|startup", "source": "...", "url": "...",
 "date_publication": "AAAA-MM-JJ", "note_brute": 7.0, "bonus": {"groupe_lvmh": 1}, "note": 8.0,
 "recommandation": "postuler", "points_forts": ["..."], "ecarts": ["..."], "mots_cles_ats": ["..."],
 "groupe_lvmh": false, "statut": "propose|a_surveiller|archive|exclu", "motif": "",
 "version_prompt": "scoring-v2"}
```

Règles : ne jamais attribuer à David une compétence absente du profil maître ; si le texte de
l'offre est trop court pour noter, l'offre n'est pas montrée (motif « texte incomplet »).
`en_bref` décrit le travail concret (missions, outils, équipe, durée), pas l'entreprise ;
`pour_toi` cite une expérience précise de David (Dior, Cogeco, Courlancy, Trezo…).
