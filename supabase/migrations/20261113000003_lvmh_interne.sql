-- Décision du 13/11 : les offres du groupe LVMH (toutes Maisons) sont cherchées et
-- analysées, mais l'outil ne postule jamais : David postule lui-même en interne.

alter type application_channel add value if not exists 'interne_lvmh';

alter table offers add column groupe_lvmh boolean not null default false;

comment on column offers.groupe_lvmh is
  'Offre du groupe LVMH : candidature interne par David uniquement, jamais par l''outil.';

-- Toute candidature sur une offre LVMH passe par le canal interne_lvmh, et le canal
-- interne_lvmh est réservé aux offres LVMH. La contrainte applications_canal_manuel
-- interdit déjà tout envoi automatique hors email : aucun envoi auto n'est possible.
create or replace function enforce_lvmh_internal()
returns trigger
language plpgsql
as $$
declare
  lvmh boolean;
begin
  select groupe_lvmh into lvmh from offers where id = new.offer_id;
  if lvmh and new.canal::text <> 'interne_lvmh' then
    raise exception 'Offre du groupe LVMH : candidature interne par David uniquement (canal interne_lvmh)'
      using errcode = 'check_violation';
  end if;
  if not lvmh and new.canal::text = 'interne_lvmh' then
    raise exception 'Le canal interne_lvmh est réservé aux offres du groupe LVMH'
      using errcode = 'check_violation';
  end if;
  return new;
end $$;

create trigger applications_lvmh_interne before insert or update of canal, offer_id on applications
  for each row execute function enforce_lvmh_internal();
