# Copilote Candidatures

Outil qui trouve chaque jour les offres qui collent au profil de David, prépare un dossier
complet pour les meilleures, attend sa validation, envoie ce qui peut l'être et suit chaque
candidature jusqu'à la réponse. Spécification complète : [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).

**Tableau de bord :** https://claude.ai/artifact/QngVuEMvQQTe5yhy1Pqgsg (privé, téléphone et ordinateur)
— offres du jour, pipeline, historique, réglages. Source : `dashboard/index.html`.

## Postuler en 5 minutes

1. Dans le tableau de bord, clique **« Préparer le dossier »** sur une offre qui te plaît.
2. Vers 12 h 30 ou 18 h 30 (sinon le lendemain matin), le dossier est prêt : CV Canva ciblé
   et son PDF, portfolio, lettre si utile, message d'approche, réponse « Pourquoi ce poste ? ».
3. Clique **« Postuler : kit prêt »** : télécharge le CV et le portfolio, copie la lettre, ouvre l'offre et
   colle les réponses du formulaire (tes infos sont dans Réglages), copie le message.
4. Clique **« J'ai postulé »** : la relance est préparée pour J+7, puis J+14.
5. Si tu décroches un entretien, passe l'offre en « Entretien » : une fiche de préparation
   est rédigée au passage suivant.

Les offres LVMH n'ont jamais de dossier : tu postules en interne.

**Chaque matin à 6 h 58** (heure de Paris), une tâche planifiée suit `prompts/routine-quotidienne.md` :
recherche, notation, écriture dans le tableau de bord, dossiers demandés, rapport et email.

## Structure

```
CAHIER_DES_CHARGES.md        spécification (décisions et résultats de la phase 0 inclus)
profil/
  profil-maitre.md           source de vérité unique (zéro invention)
  perimetre.yaml             axes, zones, exclusions, seuils, entreprises cibles
  regles.yaml                garde-fous de contenu et d'envoi, vérifiés par le code
prompts/
  routine-quotidienne.md     procédure suivie chaque matin par la tâche planifiée
  scoring.md                 grille de notation v1 (exclusions, note /10, bonus, recommandation)
  generation-dossier.md      CV Canva ciblé + PDF, lettre, message, pitch, fiche (v1)
  preparation-entretien.md   fiche de préparation d'entretien (v1)
dashboard/index.html         tableau de bord (Artifact avec base de données)
dossiers/                    dossiers de candidature préparés
donnees/offres.csv           toutes les offres vues et notées (déduplication)
rapports/AAAA-MM-JJ.md       rapport quotidien
supabase/
  migrations/                schéma : 6 tables métier + settings, RLS, bucket « documents »
  tests/socle_test.sql       tests des garde-fous SQL
scripts/test-db.sh           lance migrations + tests sur un PostgreSQL local jetable
scripts/offres.py            déduplication des offres (même empreinte que la base)
```

## Garde-fous codés dans la base

| Règle | Mécanisme |
|---|---|
| Rien ne part sans approbation horodatée | contrainte `applications_envoi_approuve` |
| Jamais deux candidatures au même poste | `unique (offer_id)` + `dedup_hash` (entreprise + intitulé normalisés) |
| Pas de bot LinkedIn / Indeed | contrainte `applications_canal_manuel` (envoi auto = email uniquement) |
| Plafond d'envois automatiques par jour | trigger `applications_send_cap` (réglage `envoi.plafond_envois_auto_jour`) |
| Alerte même entreprise < 30 jours | vue `v_alertes_meme_entreprise` |
| Motif obligatoire en cas de rejet | contrainte `applications_rejet_motif` |
| Groupe LVMH : candidature interne par David uniquement | trigger `applications_lvmh_interne` (canal `interne_lvmh`, aucun envoi auto) |
| Traçabilité totale | trigger `applications_log` → table `events` à chaque changement de statut |
| Relance J+7 programmée à l'envoi | trigger `applications_follow_up` |

## Tester le schéma

```bash
scripts/test-db.sh
```

## Mettre en place Supabase

1. Créer le projet (offre gratuite, région UE).
2. Appliquer les migrations : `supabase link` puis `supabase db push`, ou coller les fichiers
   de `supabase/migrations/` dans l'éditeur SQL, dans l'ordre.
3. Authentication → Providers → Email : **désactiver les inscriptions** (« Allow new users to
   sign up »), puis créer à la main le seul compte, celui de David. Les politiques RLS donnent
   tout l'accès à « authenticated » : c'est ce réglage qui réserve le dashboard à David.
4. Reporter l'URL et les clés dans les secrets (voir `.env.example`), jamais dans le code.
