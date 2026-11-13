-- Copilote Candidatures — socle de la base (phase 1)
-- Six tables métier (offers, scores, applications, documents, events, questions)
-- + une table settings pour les réglages modifiables depuis le dashboard.
-- Les garde-fous d'envoi sont codés ici (contraintes et triggers), pas seulement
-- dans les prompts.

set check_function_bodies = off;

-- ---------------------------------------------------------------------------
-- Types
-- ---------------------------------------------------------------------------
create type offer_source as enum (
  'france_travail', 'alerte_email', 'page_carriere', 'import_manuel', 'export_lvmh'
);

create type contract_type as enum ('CDI', 'VIE', 'CDD', 'autre');

create type application_channel as enum (
  'email',               -- email direct au recruteur : seul canal envoyable par l'outil
  'ats',                 -- Workday, Taleo, SmartRecruiters... : kit, David clique
  'linkedin',            -- jamais de bot
  'indeed',              -- jamais de bot
  'vie_business_france', -- kit en anglais, David dépose
  'autre'
);

create type application_status as enum (
  'question',         -- bloqué : une info manque, question posée à David
  'a_valider',        -- dossier prêt, attend la relecture de David
  'modif_demandee',   -- David a demandé une modification, régénération en cours
  'prete_a_envoyer',  -- approuvé, en attente d'envoi (auto ou par David)
  'envoyee',
  'relance',
  'entretien',
  'offre',
  'refus',
  'sans_reponse',
  'rejetee'           -- rejeté par David à la validation (avec motif)
);

create type send_mode as enum ('auto', 'manuel');

create type recommendation as enum ('postuler', 'postuler_en_compensant', 'passer');

create type document_type as enum ('cv', 'lm', 'message', 'kit_ats', 'portfolio', 'relance');

create type event_type as enum (
  'creee', 'approuvee', 'modif_demandee', 'rejetee', 'envoyee', 'relancee',
  'reponse', 'entretien', 'statut', 'note', 'question'
);

-- ---------------------------------------------------------------------------
-- Fonctions utilitaires
-- ---------------------------------------------------------------------------

-- Normalisation pour la déduplication : minuscules, sans accents, sans ponctuation,
-- espaces compactés. IMMUTABLE pour pouvoir servir dans une colonne générée.
create or replace function normalize_text(t text)
returns text
language sql
immutable
parallel safe
as $$
  select trim(regexp_replace(
           regexp_replace(
             -- majuscules accentuées traduites explicitement : lower() ne les
             -- convertit pas sous une collation « C »
             lower(translate(coalesce(t, ''),
                       'àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸ',
                       'aaaaaaceeeeiiiinooooouuuuyyaaaaaaceeeeiiiinooooouuuuyy')),
             '[^a-z0-9]+', ' ', 'g'),
           '\s+', ' ', 'g'))
$$;

-- ---------------------------------------------------------------------------
-- settings : réglages modifiables depuis l'écran Réglages
-- (surcharge les valeurs par défaut de profil/perimetre.yaml)
-- ---------------------------------------------------------------------------
create table settings (
  key        text primary key,
  value      jsonb not null,
  updated_at timestamptz not null default now()
);

comment on table settings is
  'Surcharges de profil/perimetre.yaml. Clé en notation pointée, ex. scoring.seuil.';

insert into settings (key, value) values
  ('scoring.seuil',                         '6'),
  ('scoring.passe_droit',                   '8'),
  ('scoring.plafond_dossiers_jour',         '5'),
  ('exclusions.experience_max_annees',      '4'),
  ('envoi.plafond_envois_auto_jour',        '10'),
  ('envoi.alerte_meme_entreprise_jours',    '30'),
  ('envoi.relances_jours',                  '[7, 14]'),
  ('entreprises.cibles',                    '[]');

create or replace function setting_int(k text, fallback int)
returns int
language sql
stable
as $$
  select coalesce((select (value #>> '{}')::int from settings where key = k), fallback)
$$;

-- Date du jour à Paris (les plafonds quotidiens suivent l'heure de Paris)
create or replace function today_paris()
returns date
language sql
stable
as $$ select (now() at time zone 'Europe/Paris')::date $$;

create or replace function set_updated_at()
returns trigger
language plpgsql
as $$
begin
  new.updated_at := now();
  return new;
end $$;

create trigger settings_updated_at before update on settings
  for each row execute function set_updated_at();

-- ---------------------------------------------------------------------------
-- offers
-- ---------------------------------------------------------------------------
create table offers (
  id                uuid primary key default gen_random_uuid(),
  source            offer_source not null,
  source_ref        text,                      -- id chez la source (France Travail, message Gmail...)
  url               text,
  entreprise        text not null,
  intitule          text not null,
  lieu              text,
  pays              text,
  contrat           contract_type,
  langue            text check (langue in ('fr', 'en', 'autre')),
  texte             text,
  canal_detecte     application_channel,
  axe               text check (axe in ('data_bi', 'finance', 'supply_chain', 'startup')),
  date_publication  date,
  date_collecte     timestamptz not null default now(),
  lien_actif        boolean,                   -- vérifié avant génération du dossier
  lien_verifie_le   timestamptz,
  dedup_hash        text generated always as (
                      md5(normalize_text(entreprise) || '|' || normalize_text(intitule))
                    ) stored,
  constraint offers_dedup_unique unique (dedup_hash)
);

comment on column offers.dedup_hash is
  'Déduplication entreprise + intitulé : une même offre vue par deux sources n''est stockée qu''une fois.';

create index offers_date_collecte_idx on offers (date_collecte desc);
create index offers_entreprise_norm_idx on offers (normalize_text(entreprise));

-- ---------------------------------------------------------------------------
-- scores (plusieurs versions possibles par offre : on garde l'historique)
-- ---------------------------------------------------------------------------
create table scores (
  id              uuid primary key default gen_random_uuid(),
  offer_id        uuid not null references offers (id) on delete cascade,
  note            numeric(3, 1) not null check (note between 0 and 10),
  note_brute      numeric(3, 1) check (note_brute between 0 and 10), -- avant bonus
  bonus           jsonb not null default '{}'::jsonb,                 -- ex. {"groupe_lvmh": 1}
  points_forts    text[] not null default '{}',
  ecarts          text[] not null default '{}',
  recommandation  recommendation not null,
  mots_cles_ats   text[] not null default '{}',
  exclusion       text,                     -- motif si exclue par un filtre automatique
  version_prompt  text not null,
  created_at      timestamptz not null default clock_timestamp()  -- distingue 2 scores d'une même transaction
);

create index scores_offer_idx on scores (offer_id, created_at desc);

-- Dernier score de chaque offre
create view v_offer_latest_score
with (security_invoker = true) as
select distinct on (s.offer_id) s.*
from scores s
order by s.offer_id, s.created_at desc;

-- ---------------------------------------------------------------------------
-- applications
-- ---------------------------------------------------------------------------
create table applications (
  id                 uuid primary key default gen_random_uuid(),
  offer_id           uuid not null references offers (id) on delete restrict,
  statut             application_status not null default 'a_valider',
  canal              application_channel not null,
  mode_envoi         send_mode,
  approuve_le        timestamptz,            -- approbation explicite et horodatée
  date_envoi         timestamptz,
  contact_nom        text,
  contact_role       text,
  contact_email      text,
  contact_linkedin   text,
  notes              text,
  motif_rejet        text,
  prochaine_relance  date,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now(),

  -- Jamais deux candidatures au même poste
  constraint applications_offer_unique unique (offer_id),

  -- Rien ne part sans validation : tout statut « envoyé » exige une approbation
  -- horodatée et une date d'envoi
  constraint applications_envoi_approuve check (
    statut not in ('prete_a_envoyer', 'envoyee', 'relance', 'entretien', 'offre', 'refus', 'sans_reponse')
    or approuve_le is not null
  ),
  constraint applications_envoi_date check (
    statut not in ('envoyee', 'relance', 'entretien', 'offre', 'refus', 'sans_reponse')
    or date_envoi is not null
  ),

  -- Pas de bot : seul l'email direct peut être envoyé automatiquement
  constraint applications_canal_manuel check (
    mode_envoi is distinct from 'auto' or canal = 'email'
  ),

  constraint applications_rejet_motif check (
    statut <> 'rejetee' or motif_rejet is not null
  )
);

create index applications_statut_idx on applications (statut);
create index applications_relance_idx on applications (prochaine_relance)
  where statut in ('envoyee', 'relance');

create trigger applications_updated_at before update on applications
  for each row execute function set_updated_at();

-- Plafond d'envois automatiques par jour (heure de Paris)
create or replace function enforce_daily_send_cap()
returns trigger
language plpgsql
as $$
declare
  cap   int := setting_int('envoi.plafond_envois_auto_jour', 10);
  sent  int;
begin
  if new.mode_envoi = 'auto' and new.statut = 'envoyee'
     and (tg_op = 'INSERT' or old.statut is distinct from 'envoyee') then
    select count(*) into sent
    from applications
    where mode_envoi = 'auto'
      and date_envoi is not null
      and (date_envoi at time zone 'Europe/Paris')::date = today_paris()
      and id <> new.id;
    if sent >= cap then
      raise exception 'Plafond d''envois automatiques atteint (% par jour)', cap
        using errcode = 'check_violation';
    end if;
  end if;
  return new;
end $$;

create trigger applications_send_cap before insert or update on applications
  for each row execute function enforce_daily_send_cap();

-- Programmation des relances J+7 / J+14 à l'envoi
create or replace function schedule_follow_up()
returns trigger
language plpgsql
as $$
begin
  if new.statut = 'envoyee' and (tg_op = 'INSERT' or old.statut is distinct from 'envoyee')
     and new.prochaine_relance is null then
    new.prochaine_relance := (new.date_envoi at time zone 'Europe/Paris')::date + 7;
  end if;
  return new;
end $$;

create trigger applications_follow_up before insert or update on applications
  for each row execute function schedule_follow_up();

-- ---------------------------------------------------------------------------
-- documents
-- ---------------------------------------------------------------------------
create table documents (
  id                   uuid primary key default gen_random_uuid(),
  application_id       uuid not null references applications (id) on delete cascade,
  type                 document_type not null,
  version              int not null default 1 check (version >= 1),
  langue               text check (langue in ('fr', 'en')),
  contenu              text,     -- texte de la LM, du message, du kit ATS
  fichier_path         text,     -- chemin dans le bucket Storage « documents »
  lien_canva           text,
  canva_design_id      text,
  fiche_modifications  text,     -- ce qui a changé par rapport au CV de base, et pourquoi
  approuve_le          timestamptz,
  created_at           timestamptz not null default now(),
  constraint documents_version_unique unique (application_id, type, version)
);

create index documents_application_idx on documents (application_id);

-- ---------------------------------------------------------------------------
-- events : historique complet de chaque candidature
-- ---------------------------------------------------------------------------
create table events (
  id              uuid primary key default gen_random_uuid(),
  application_id  uuid not null references applications (id) on delete cascade,
  date            timestamptz not null default clock_timestamp(),
  type            event_type not null,
  detail          jsonb not null default '{}'::jsonb
);

create index events_application_idx on events (application_id, date desc);

-- Journalisation automatique : création et chaque changement de statut
create or replace function log_application_event()
returns trigger
language plpgsql
as $$
declare
  t event_type;
begin
  if tg_op = 'INSERT' then
    insert into events (application_id, type, detail)
    values (new.id, 'creee', jsonb_build_object('statut', new.statut, 'canal', new.canal));
    return new;
  end if;

  if new.statut is distinct from old.statut then
    t := case new.statut
           when 'prete_a_envoyer' then 'approuvee'
           when 'modif_demandee'  then 'modif_demandee'
           when 'rejetee'         then 'rejetee'
           when 'envoyee'         then 'envoyee'
           when 'relance'         then 'relancee'
           when 'entretien'       then 'entretien'
           when 'question'        then 'question'
           else 'statut'
         end;
    insert into events (application_id, type, detail)
    values (new.id, t, jsonb_strip_nulls(jsonb_build_object(
      'de', old.statut, 'vers', new.statut,
      'mode_envoi', new.mode_envoi, 'motif', new.motif_rejet)));
  end if;
  return new;
end $$;

create trigger applications_log after insert or update on applications
  for each row execute function log_application_event();

-- ---------------------------------------------------------------------------
-- questions : infos manquantes posées à David (zéro invention)
-- ---------------------------------------------------------------------------
create table questions (
  id              uuid primary key default gen_random_uuid(),
  application_id  uuid not null references applications (id) on delete cascade,
  question        text not null,
  reponse         text,
  date            timestamptz not null default now(),
  repondu_le      timestamptz
);

create index questions_ouvertes_idx on questions (application_id) where reponse is null;

-- ---------------------------------------------------------------------------
-- Vues pour le dashboard et le digest
-- ---------------------------------------------------------------------------

-- Alerte : deux candidatures à la même entreprise en moins de N jours
create view v_alertes_meme_entreprise
with (security_invoker = true) as
select
  a.id               as application_id,
  b.id               as autre_application_id,
  oa.entreprise      as entreprise,
  ob.intitule        as autre_intitule,
  b.statut           as autre_statut,
  coalesce(b.date_envoi, b.created_at) as autre_date
from applications a
join offers oa on oa.id = a.offer_id
join applications b on b.id <> a.id and b.statut <> 'rejetee'
join offers ob on ob.id = b.offer_id
where normalize_text(oa.entreprise) = normalize_text(ob.entreprise)
  and abs(extract(epoch from coalesce(a.date_envoi, a.created_at) - coalesce(b.date_envoi, b.created_at)))
      < setting_int('envoi.alerte_meme_entreprise_jours', 30) * 86400;

-- Compteurs de l'écran « Aujourd'hui »
create view v_aujourdhui
with (security_invoker = true) as
select
  count(*) filter (where statut = 'a_valider')                          as a_valider,
  count(*) filter (where statut = 'question')                           as questions,
  count(*) filter (where statut = 'prete_a_envoyer' and canal <> 'email') as a_envoyer_par_moi,
  count(*) filter (where statut in ('envoyee', 'relance')
                   and prochaine_relance <= today_paris())               as relances_du_jour,
  (select count(*) from events e
    where e.type in ('reponse', 'entretien')
      and (e.date at time zone 'Europe/Paris')::date >= today_paris() - 1) as reponses_recentes
from applications;

-- ---------------------------------------------------------------------------
-- Sécurité : RLS partout. Le dashboard n'a qu'un utilisateur (David) :
-- les inscriptions publiques doivent être désactivées dans Supabase Auth.
-- La tâche planifiée utilise la clé service_role (qui contourne RLS).
-- ---------------------------------------------------------------------------
do $$
declare
  t text;
begin
  foreach t in array array['settings', 'offers', 'scores', 'applications', 'documents', 'events', 'questions']
  loop
    execute format('alter table %I enable row level security', t);
    execute format('create policy %I on %I for all to authenticated using (true) with check (true)',
                   t || '_proprietaire', t);
  end loop;
end $$;
