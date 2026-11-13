# Routine quotidienne — recherche, notation, rapport (v1)

Lancée chaque matin par une tâche planifiée. Objectif : trouver les nouvelles offres qui
collent au profil de David, les noter et lui envoyer un rapport lisible en 2 minutes.

**Interdits absolus :** ne jamais postuler (et en particulier jamais aux offres du groupe
LVMH, auxquelles David postule lui-même en interne), ne jamais contacter un recruteur, ne jamais se
connecter à LinkedIn ou Indeed (lire seulement les alertes reçues par email), ne jamais
inventer une offre, une date ou un lien. Une offre dont le lien n'a pas pu être vérifié est
signalée comme telle.

## 0. Préparation

Dans le dépôt `copilote-candidatures` :

1. `git pull` pour partir de la dernière version.
2. Lire `profil/profil-maitre.md`, `profil/perimetre.yaml`, `prompts/scoring.md`.
3. Noter la date du jour (heure de Paris) : `AAAA-MM-JJ`.

## 1. Sourcing (viser 30 à 60 offres candidates)

Travailler axe par axe dans l'ordre de priorité (Data/BI, Finance, Supply Chain, Startup),
zone par zone (Suisse, Paris, Lyon, VIE), avec les intitulés de `perimetre.yaml`.

**a. Alertes Gmail** (2 derniers jours) :
`newer_than:2d from:(jobalerts-noreply@linkedin.com OR jobs-noreply@linkedin.com OR apec.fr OR welcometothejungle.com OR jobteaser.com OR jobs.ch OR jobup.ch OR businessfrance.fr)`
Lire chaque fil en entier et extraire les offres (intitulé, entreprise, lieu, lien).

**b. Sites d'emploi** (WebFetch), pages de résultats triées par date :
- Suisse : jobup.ch, jobs.ch, datacareer.ch
- France : welcometothejungle.com, apec.fr, candidat.francetravail.fr, hellowork.com, cadremploi.fr
- VIE : mon-vie-via.businessfrance.fr
- LVMH : lvmh.com (offres du groupe et des Maisons)
Si un site ne répond pas (domaine non autorisé), passer au suivant et le noter dans le rapport.

**c. Recherche web** (WebSearch, mode standard) pour compléter, avec des requêtes ciblées,
par exemple `"Data Analyst" Genève site:jobup.ch`, `"FP&A Analyst" Paris CDI`,
`VIE "Financial Analyst" 2027`, et une requête par entreprise cible
(`<entreprise> careers data analyst`). Les résultats de recherche sont souvent anciens :
ouvrir l'offre pour vérifier la date et qu'elle est toujours en ligne ; si c'est impossible,
la garder avec la mention « lien non vérifié ».

Écrire chaque offre candidate, une par ligne, dans `/tmp/candidates.jsonl`
(`entreprise`, `intitule`, `lieu`, `pays`, `url`, `source`, `date_publication` si connue).

## 2. Déduplication

```bash
python3 scripts/offres.py filtrer < /tmp/candidates.jsonl > /tmp/nouvelles.jsonl
```

Seules les offres de `/tmp/nouvelles.jsonl` sont notées (les autres ont déjà été vues un jour
précédent).

## 3. Notation

Pour chaque nouvelle offre : ouvrir le texte complet quand c'est possible, appliquer
`prompts/scoring.md` (filtres d'exclusion, puis note, bonus, recommandation) et écrire le
résultat JSON dans `/tmp/notees.jsonl`. Statut :
- `propose` : note ≥ seuil, retenue dans le rapport ;
- `a_surveiller` : note entre seuil − 1 et seuil, ou texte incomplet ;
- `archive` : note plus basse ;
- `exclu` : filtre d'exclusion, avec le motif.

Les offres du groupe LVMH (`groupe_lvmh: true`) sont mises à part : toutes celles au-dessus
du seuil vont dans la rubrique « Groupe LVMH » du rapport, hors sélection du jour.

Sélection du jour (hors LVMH) : toutes les offres à 8/10 ou plus, puis les meilleures autres offres
au-dessus du seuil jusqu'à 5 au total. Les offres au-dessus du seuil non retenues passent
en `a_surveiller`.

## 4. Enregistrement

```bash
python3 scripts/offres.py ajouter < /tmp/notees.jsonl
```

## 5. Rapport `rapports/AAAA-MM-JJ.md`

```markdown
# Rapport du JJ/MM/AAAA

**N offres proposées** · X candidates trouvées · Y nouvelles · Z exclues

## À regarder aujourd'hui
### 1. <Intitulé> — <Entreprise> (<Lieu>) · **8,5/10** · postuler
- Pourquoi : <2 ou 3 points forts>
- Écarts : <écart et comment le compenser>
- Canal : <email / ATS / LinkedIn / VIE> · Langue : <fr/en> · Publiée le <date>
- Lien : <url> (ou « lien non vérifié »)

## Groupe LVMH — à postuler en interne par David
<même format que ci-dessus ; l'outil ne prépare rien d'autre pour ces offres>

## À surveiller
| Note | Poste | Entreprise | Lieu | Lien |

## Exclues (résumé)
<motifs les plus fréquents, en une ligne chacun>

## Sources
<ce qui a marché, ce qui a été bloqué>
```

S'il n'y a aucune offre au-dessus du seuil, le dire clairement en tête du rapport.

## 6. Publication

```bash
git add rapports/ donnees/ && git commit -m "Rapport du AAAA-MM-JJ" && git push
```

## 7. Envoi à David

Envoyer un email (connecteur Gmail, `send_message`) à l'adresse Gmail de David, sans pièce
jointe :
- Objet : `Copilote · N offres le JJ/MM` (ou `Copilote · rien de nouveau le JJ/MM`)
- Corps en texte simple : les offres proposées (poste, entreprise, lieu, note, lien), puis
  les offres du groupe LVMH sous le titre « Groupe LVMH (candidature interne) », une ligne
  sur les offres à surveiller, puis le lien vers le rapport :
  `https://github.com/pavidderkins-gif/copilote-candidatures/blob/main/rapports/AAAA-MM-JJ.md`

Si l'envoi échoue, créer un brouillon avec le même contenu et le signaler dans le rapport.
Terminer par un résumé de 3 lignes dans la conversation.
