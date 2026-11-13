# Prompts (versionnés)

Chaque prompt porte un numéro de version, enregistré dans `scores.version_prompt` pour savoir
quelle version a produit quelle note.

| Fichier (phase 2) | Rôle | Statut |
|---|---|---|
| `routine-quotidienne.md` | Recherche, notation et rapport de chaque matin | v1 |
| `scoring.md` | Notation : exclusions, note /10, bonus, recommandation | v1, rédigée d’après le cahier des charges |
| `generation-cv.md` | Textes du CV ciblé + fiche de modifications | à écrire |
| `generation-lm.md` | Lettre de motivation | à écrire |
| `message-approche.md` | Message LinkedIn ou email + contact | à écrire |
| `relance.md` | Relances J+7 et J+14 | à écrire |
| `entretien.md` | Mode E du coach : préparation d’entretien | texte de David si disponible, sinon rédigé d’après le cahier des charges |

Tous les prompts de génération lisent `profil/profil-maitre.md` et `profil/regles.yaml`, et
renvoient une question pour David au lieu d'inventer une information manquante.
