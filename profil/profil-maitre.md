# Profil maître — David Perkins

> Source de vérité unique. Tout contenu généré (CV, lettre, message, relance) doit venir de ce fichier.
> Une info absente ici devient une **question pour David**, jamais un trou comblé au hasard.
> Version du 13/11/2026 (copiée telle quelle depuis le cahier des charges).


## 1. Identité et disponibilité

- Ingénieur Arts et Métiers (ENSAM) : diplôme obtenu à la fin du stage
  Dior (janvier 2027).

- Master of Entrepreneurship and Innovation, University of Queensland
  (UQ Business School), mineure Business Analytics : diplôme obtenu.

- Bilingue français-anglais (mère française, père anglais). TOEFL iBT :
  niveau C2 en lecture, écoute et expression orale. Ne parle pas
  allemand.

- Nationalité : pas de nationalité britannique (confirmé le 13/11/2026) ; un VIE au
  Royaume-Uni est donc possible.

- Australie : pas de droit de travail pour l'instant (14/11/2026). David pense être éligible
  au visa post-études (Temporary Graduate, subclass 485) après son master à UQ (fin en
  juillet 2026) : non confirmé, délai de dépôt à vérifier sur le site officiel.

- Disponible en CDI à partir de début février 2027. Le stage Dior se
  termine le 15 janvier 2027.

## 2. Expériences et réalisations

**Parfums Christian Dior – Supply Chain Data & Analytics Engineer
(stage, juillet 2026 à janvier 2027, Saint-Jean-de-Braye)**

Outils utilisés pendant le stage : SAP, Power BI, Excel / VBA (précisé par David le 16/11/2026).

**Outil 1 – Suivi des lancements de nouveaux produits (livré)** — description
précisée par David le 16/11/2026 :

- Outil Power BI (extractions Excel possibles) qui suit le lancement de tous
  les nouveaux produits à partir des prévisions de ventes.

- Prend en entrée les prévisions de ventes et toutes les données articles ;
  compare le plan de production au plan de besoins ; donne les besoins en
  articles de conditionnement et en matières premières.

- Suit chaque lancement jusqu'à sa date de mise au comptoir (on-counter
  date) (confirmé par David le 16/11/2026).

- C'est aussi l'outil de « prévision pour les lancements pays et marchés »
  noté le 13/11 : un seul et même outil (confirmé par David le 16/11/2026).

- Une quinzaine de dashboards construits sur une quinzaine de tables de
  référence (jusqu'à 1 million de lignes chacune).

- Utilisé pour tous les nouveaux produits, sur les sites de Chartres,
  Saint-Jean-de-Braye et Pudong (Chine).

- Gain d'au moins 1h30 par projet lors de chaque lancement.

- Plus de 50 utilisateurs clés, des opérateurs à l'Industrial Supply Chain Director (directeur supply chain
  industrielle ; confirmé par David le 13/11/2026).

- Flux de données venant de SAP, SharePoint et Excel. Cycle Dev / Test /
  Prod. Gestion des accès et de la gouvernance. Utilisation de Google
  Cloud Platform (GCP).

**Outil 2 – Exactitude des fiches articles (en cours)** — décrit par David le
16/11/2026 :

- Outil Power BI qui contrôle l'exactitude des fiches articles, pour tous
  les articles de conditionnement et toutes les matières premières.

- Calcule la classe ABC de chaque article et la compare à la classe ABC
  renseignée (confirmé par David le 16/11/2026).

- Vérifie la cohérence du statut des articles de conditionnement et des
  matières premières avec celui du produit fini auquel ils correspondent,
  pour suivre plus précisément les fins de vie des articles.

- Résultats chiffrés de l'outil 2 à préciser (nombre d'articles contrôlés,
  écarts trouvés).

**Cogeco – Consultant data et finance indépendant (depuis août 2026, fin
prévue en décembre 2026)**

- Outil Excel et Power BI de consolidation de la trésorerie
  prévisionnelle, pour une holding et ses 10 filiales.

- Dashboards pour la direction et les banques, export PDF automatique,
  archivage mensuel sur OneDrive.

- A porté toute la relation client : proposition commerciale, devis,
  planning, livraison. Mission de 13 jours vendue 2 600 € HT.

- Avancement conforme au planning.

**Courlancy Santé – Consultant data, via la Junior-Entreprise de l'ENSAM
(mai 2025 à janvier 2026)**

- Nouveau système de calcul des salaires (masse salariale de 34 M€,
  modèle salaire de base + ECR) pour 10 900 salariés.

- Simulations pour aider la direction à fixer les salaires de base et
  l'ancienneté.

- Outil utilisé en production par la direction et les responsables RH.

- Reporting mensuel d'aide à la décision pour la direction ; rapprochement des écarts
  entre l'ancien et le nouveau modèle (confirmé par David le 13/11/2026).

**Gadz Cours Particuliers – Fondateur et gérant (février à août 2025)**

- Plus de 30 clients et plus de 30 professeurs recrutés. Marketing 100 % organique.
  Activité menée seul de bout en bout.

- Back-office Excel, facturation et gestion de la trésorerie (cash management)
  (confirmé par David le 13/11/2026).

**Australian Venue Co. – Babylon, Brisbane (septembre 2025 à juillet
2026)**

- Responsable de section lors de grands événements (plus de 600
  couverts). A formé les nouvelles recrues. A servi des clients VIP,
  dont des ambassadeurs.

**Asygn – Stage (juillet et août 2024, Grenoble)**

- Machine learning : modèle OCR sur MNIST (70 000 images), détection
  jour/nuit avec OpenCV et scikit-learn.

- Data : optimisation de requêtes SQL, classification de trajectoires en
  Python, intégration dans Grafana.

**Trezo – Projet personnel, appli de finances perso (depuis le
30/10/2026)**

- Application web installable (PWA) de finances personnelles, conçue et
  livrée seul avec Claude Code : spécification écrite d'abord, puis 74
  commits en 14 jours, après des problèmes de connexion de Fortuneo sur
  Finary.

- Stack : Next.js 15 (App Router), React 19, TypeScript (environ 21 000
  lignes), Tailwind CSS 4, Recharts ; Supabase (PostgreSQL, Row Level
  Security, 19 migrations SQL, hébergé en Irlande) ; Vercel (Dublin),
  déploiement continu depuis GitHub, tâches planifiées (cron). 0 €
  d'hébergement.

- Intégrations : synchronisation bancaire DSP2 via Enable Banking (JWT
  RS256, clés chiffrées en AES-256-GCM), cours de bourse et crypto
  (Yahoo Finance, CoinGecko), e-mails (SMTP), notifications push (Web
  Push).

- Serveur MCP codé pour interroger ses finances directement depuis
  Claude.

- Fonctions clés : rapprochement bancaire automatique entre saisies
  manuelles et lignes bancaires, avec signalement des écarts ;
  catégorisation apprise de l'historique de l'utilisateur ; budget
  mensuel selon la règle 50/30/20 avec objectif réglable ; bilans
  automatiques hebdomadaires et mensuels par e-mail et notification.

- 5 utilisateurs actifs.

- À mettre en avant pour les postes data/finance, fintech, startup et IA
  (projet phare pour Finary).

**Enseignement :** professeur particulier sur Superprof (20 h par
semaine, 40 élèves au total) et chargé de cours d'anglais professionnel
à l'IPSSI (50 étudiants).

**Association :** trésorier de l'association de voile de l'ENSAM (budget
d'environ 20 000 €, financement des compétitions, catégorisation des
dépenses, déclarations annuelles).

## 3. Compétences

- Techniques : Power BI (modélisation, DAX), Excel/VBA, SQL, Python,
  SAP, GCP, Grafana, IA générative.

- Humaines : gestion de projet, relation client, faire le lien entre les
  métiers et la technique, management, pédagogie, grosse capacité de
  travail et d'organisation.

- Certifications : Leading with Generative AI (HBS Online), Claude 101
  et Introduction to Agent Skills (Anthropic).

## 4. Motivations

- Ce qui le motive : créer, être autonome, porter un projet de bout en
  bout, la dimension humaine (aider, manager), apprendre vite.

- Ce qui le freine : la lenteur du changement dans les grands groupes,
  et la prise de risque du freelance.

- Intérêts forts : la banque, l'IA, le groupe LVMH.

## 5. Contraintes géographiques

- CDI : d'abord la Suisse (postes en français ou en anglais, pas en
  allemand), puis Paris, puis Lyon. L'Australie (de préférence
  Sydney) si l'opportunité est bonne.

- VIE : tous pays, priorité aux pays anglophones, sauf la Chine, le
  Japon et la Corée.

- Salaire : pas un critère de recherche. Prétentions à indiquer dans les formulaires
  (13/11/2026) : France 43 000 – 46 000 € bruts annuels ; Suisse 80 000 – 90 000 CHF
  bruts annuels selon le canton et le poste (estimation de Claude validée par David).

## 6. Ambitions

- Objectif n°1 : l'analyse de données pour aider les entreprises à
  prendre des décisions, ou l'analyse de données financières.

- Conseil et ingénieur d'affaires : plus recherchés activement, car il a
  déjà plusieurs pistes et entretiens en cours dans ces métiers.

- Positionnement : premier emploi, enrichi de plusieurs missions data en
  freelance et via la Junior-Entreprise.

## 7. Règles de présentation

- Ne pas mettre en avant le classement du premier semestre à l'ENSAM.

- Email ENSAM sur le CV, pas d'adresse postale.

- Références (liste donnée par David le 16/11/2026, à mettre sous chaque
  lettre de motivation) :
  - Mathurine Moreau – RH Supply Chain, Parfums Christian Dior –
    mamoreau@diormail.com
  - Nicolas Bouchet – Industrial Supply Chain Director, Parfums Christian
    Dior – nbouchet@diormail.com
  - Peggy Lapeyronie – Excellence opérationnelle, tutrice de stage, Parfums
    Christian Dior – plapeyronie@diormail.com
  - Mathilde Goutille – Présidente, Cogeco –
    mathilde.goutille@cogeco-promotion.fr
  - Autre référence possible (pas dans la liste du 16/11) : Nicole Smith
    (manager, Babylon Brisbane).

