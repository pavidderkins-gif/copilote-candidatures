# Notation d'une offre — version v1 (13/11/2026)

> Rédigée d'après le cahier des charges (le « mode B du coach » n'a pas été fourni).
> La version est enregistrée avec chaque note (`version_prompt: scoring-v1`).

Entrées : le texte complet de l'offre, `profil/profil-maitre.md`, `profil/perimetre.yaml`.

## 1. Filtres d'exclusion (avant toute note)

Si l'un de ces cas s'applique, l'offre est **exclue** : statut `exclu`, motif noté, pas de note.

- Poste de conseil : cabinet de conseil, ESN/SSII, intitulé contenant « consultant » ou « consulting ».
- Ingénieur d'affaires, ingénieur commercial, business developer, key account.
- Expérience exigée supérieure à `exclusions.experience_max_annees` (4 ans).
- Allemand exigé (même « souhaité fortement »).
- Zone hors périmètre : ni Suisse, ni Paris/Île-de-France, ni Lyon, ni VIE, ni Australie.
- VIE en Chine, au Japon ou en Corée.
- Site isolé, loin d'une ville.
- Stage, alternance ou poste étudiant (David cherche un CDI ou un VIE à partir de février 2027).
- Offre expirée ou publiée il y a plus de 30 jours.

## 2. Note brute sur 10

| Critère | Points | Ce qui donne le maximum |
|---|---|---|
| Missions | 0 à 3 | Analyse de données pour aider à décider, ou analyse financière (priorité n°1) : dashboards, modélisation, prévision, reporting de direction |
| Compétences | 0 à 2 | La plupart des compétences demandées sont dans le profil : Power BI/DAX, SQL, Python, Excel/VBA, SAP, GCP |
| Séniorité | 0 à 2 | Jeune diplômé ou 0 à 2 ans ; 1 point pour 2 à 4 ans |
| Zone | 0 à 1 | Suisse 1 ; Paris 0,75 ; VIE pays anglophone 0,75 ; Lyon 0,5 ; autre VIE 0,5 ; Australie 0,5 |
| Signaux implicites | 0 à 1,5 | Autonomie, projet de bout en bout, lien métier-technique, dimension humaine, apprentissage rapide, environnement international |
| Contrat et date | 0 à 0,5 | CDI ou VIE, démarrage compatible avec février 2027 |

## 3. Bonus (note finale plafonnée à 10)

- +1 : entreprise de `entreprises.cibles`
- +1 : groupe LVMH ou une de ses Maisons (`entreprises.groupe_lvmh_mots_cles`)
- +0,5 : banque
- +0,5 : IA (entreprise d'IA ou poste centré sur l'IA)

### Groupe LVMH

Une offre du groupe LVMH ou d'une de ses Maisons est notée normalement (bonus compris), mais
elle reçoit `"groupe_lvmh": true` et `"canal": "interne_lvmh"`. Elle n'entre pas dans les 5
dossiers du jour : elle va dans une rubrique à part du rapport. **L'outil ne postule jamais et
ne prépare aucun envoi pour ces offres : David postule lui-même en interne.**

## 4. Recommandation

- Note finale ≥ `scoring.seuil` (6) sans écart bloquant → **postuler**
- Note finale ≥ seuil avec un écart à compenser (compétence manquante, séniorité limite) → **postuler en compensant**, en disant comment compenser
- Note finale < seuil → **passer**

## 5. Sortie attendue (une ligne JSON par offre)

```json
{"entreprise": "...", "intitule": "...", "lieu": "...", "pays": "...", "contrat": "CDI|VIE|CDD|autre",
 "langue": "fr|en", "axe": "data_bi|finance|supply_chain|startup", "source": "...", "url": "...",
 "date_publication": "AAAA-MM-JJ", "note_brute": 7.0, "bonus": {"groupe_lvmh": 1}, "note": 8.0,
 "recommandation": "postuler", "points_forts": ["..."], "ecarts": ["..."], "mots_cles_ats": ["..."],
 "groupe_lvmh": false, "statut": "propose|a_surveiller|archive|exclu", "motif": "",
 "version_prompt": "scoring-v1"}
```

Règles : ne jamais attribuer à David une compétence absente du profil maître ; si le texte de
l'offre est trop court pour noter, `statut: a_surveiller` avec le motif « texte incomplet ».
