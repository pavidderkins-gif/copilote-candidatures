# Copilote Candidatures

Outil qui trouve chaque jour les offres qui collent au profil de David, prépare un dossier
complet pour les meilleures, attend sa validation, envoie ce qui peut l'être et suit chaque
candidature jusqu'à la réponse. Spécification complète : [CAHIER_DES_CHARGES.md](CAHIER_DES_CHARGES.md).

## Structure

```
CAHIER_DES_CHARGES.md        spécification (décisions et résultats de la phase 0 inclus)
profil/
  profil-maitre.md           source de vérité unique (zéro invention)
  perimetre.yaml             axes, zones, exclusions, seuils, entreprises cibles
  regles.yaml                garde-fous de contenu et d'envoi, vérifiés par le code
prompts/                     prompts de scoring, génération, relance (phase 2)
supabase/
  migrations/                schéma : 6 tables métier + settings, RLS, bucket « documents »
  tests/socle_test.sql       tests des garde-fous SQL
scripts/test-db.sh           lance migrations + tests sur un PostgreSQL local jetable
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
