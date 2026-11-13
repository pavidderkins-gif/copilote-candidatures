# Génération d'un dossier de candidature — version v1 (13/11/2026)

Entrées : l'offre (texte complet si possible), `profil/profil-maitre.md`, `profil/regles.yaml`,
`profil/perimetre.yaml` (titre_cv, langue_dossier, canva). **Jamais pour une offre LVMH.**

## 1. Langue et base du CV

- Langue = langue de l'offre (`fr` ou `en`).
- Base Canva : `canva.cv_reference_fr` pour une offre en français ; pour une offre en anglais,
  le CV anglais le plus proche de l'axe parmi les CV « EN-David-Perkins-CV-… » de Canva
  (rechercher « EN-David-Perkins-CV »), sinon traduire la base française.
- Toujours travailler sur une **copie** (`copy-design`), jamais sur l'original. Nommer la copie
  `<FR|EN>-David-Perkins-CV-<Entreprise>-<Intitulé court>`.

## 2. Ce qui change sur le CV (et rien d'autre)

1. **Titre** : « David Perkins – <intitulé du poste visé> » (règle `titre_cv`).
2. **Résumé** (3 lignes) : réécrit pour l'offre, avec 2 ou 3 mots-clés ATS de l'offre que le
   profil justifie réellement.
3. **Ordre des compétences** : la compétence la plus demandée par l'offre en premier.
4. **Puces d'expérience** : reformuler pour faire ressortir ce que l'offre demande, sans ajouter
   de fait. Les chiffres autorisés sont ceux du profil maître, et eux seuls.

Contrôles avant de valider (règles bloquantes de `regles.yaml`) : aucun fait hors profil maître,
intitulé du master UQ exact, pas de classement ENSAM, email ENSAM et pas d'adresse postale, pas
de « 2 ans d'expérience » ou plus, Courlancy via la Junior-Entreprise, pas d'allemand, langue de
l'offre. Vérifier le rendu (vignette) : rien qui déborde, tout tient sur une page.

## 3. Lettre de motivation (si l'offre la demande ou si elle apporte un vrai plus)

250 à 300 mots, dans la langue de l'offre. Structure : pourquoi cette entreprise (un fait
précis tiré de l'offre ou du site), ce que David apporte (2 preuves chiffrées du profil maître),
ce qu'il veut apprendre, disponibilité (février 2027). Signature : « Respectueusement » en
français, « Kind regards » en anglais.

## 4. Message d'approche (LinkedIn ou email, 600 caractères maximum)

Accroche liée à l'offre, une preuve, une question ouverte. Le destinataire (nom et rôle) n'est
indiqué que s'il est trouvé de façon fiable ; sinon « au recruteur ou au manager du poste ».

## 5. Fiche de modifications

Liste courte : ce qui a changé par rapport au CV de base, et pourquoi (quel élément de l'offre).

## 6. Questions bloquantes

Toute information nécessaire mais absente du profil maître devient une question pour David
(ex. prétentions salariales, permis de travail, date de démarrage exacte). Ne jamais inventer.

## 7. Enregistrement dans le dashboard

`dossiers/<dedup_hash>` : `cv_url` (lien d'édition Canva de la copie), `cv_design_id`,
`cv_titre`, `langue`, `lettre`, `message`, `fiche_modifications`, `questions` (liste),
`cree_le` (AAAA-MM-JJ), `version_prompt: "generation-v1"`.
Puis `suivi/<dedup_hash>` → `etape: "dossier_pret"`.
