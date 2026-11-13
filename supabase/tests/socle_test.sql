-- Tests du socle : à lancer sur une base vierge après les migrations.
-- Chaque bloc vérifie un garde-fou ; le script s'arrête à la première erreur.
\set ON_ERROR_STOP on
\set QUIET on

do $$
declare
  o1 uuid; o2 uuid; o3 uuid; a1 uuid; a2 uuid; n int; i int;
begin
  -- 1. Déduplication entreprise + intitulé (casse, accents, ponctuation)
  insert into offers (source, entreprise, intitule) values ('import_manuel', 'Parfums Christian Dior', 'Data Analyst') returning id into o1;
  begin
    insert into offers (source, entreprise, intitule) values ('france_travail', '  parfums christian DIOR ', 'Data  analyst!');
    raise exception 'ÉCHEC : doublon accepté';
  exception when unique_violation then null;
  end;
  begin
    insert into offers (source, entreprise, intitule) values ('france_travail', 'Société Générale', 'Contrôleur de gestion');
    insert into offers (source, entreprise, intitule) values ('france_travail', 'societe generale', 'controleur de gestion');
    raise exception 'ÉCHEC : doublon accentué accepté';
  exception when unique_violation then null;
  end;
  raise notice 'OK 1 déduplication';

  -- 2. Création → événement « creee » automatique
  insert into applications (offer_id, canal) values (o1, 'email') returning id into a1;
  select count(*) into n from events where application_id = a1 and type = 'creee';
  if n <> 1 then raise exception 'ÉCHEC : événement creee absent'; end if;
  raise notice 'OK 2 journal de création';

  -- 3. Jamais deux candidatures au même poste
  begin
    insert into applications (offer_id, canal) values (o1, 'email');
    raise exception 'ÉCHEC : 2e candidature au même poste acceptée';
  exception when unique_violation then null;
  end;
  raise notice 'OK 3 une seule candidature par poste';

  -- 4. Rien ne part sans approbation
  begin
    update applications set statut = 'envoyee', date_envoi = now() where id = a1;
    raise exception 'ÉCHEC : envoi sans approbation accepté';
  exception when check_violation then null;
  end;
  begin
    update applications set statut = 'prete_a_envoyer' where id = a1;
    raise exception 'ÉCHEC : prête à envoyer sans approbation acceptée';
  exception when check_violation then null;
  end;
  raise notice 'OK 4 approbation obligatoire';

  -- 5. Approbation puis envoi : événements + relance J+7
  update applications set statut = 'prete_a_envoyer', approuve_le = now() where id = a1;
  update applications set statut = 'envoyee', date_envoi = now(), mode_envoi = 'auto' where id = a1;
  select count(*) into n from events where application_id = a1 and type in ('approuvee', 'envoyee');
  if n <> 2 then raise exception 'ÉCHEC : événements approuvee/envoyee manquants (%)', n; end if;
  if (select prochaine_relance from applications where id = a1) <> today_paris() + 7 then
    raise exception 'ÉCHEC : relance J+7 non programmée';
  end if;
  raise notice 'OK 5 journal + relance J+7';

  -- 6. Pas de bot LinkedIn / Indeed
  insert into offers (source, entreprise, intitule) values ('alerte_email', 'Finary', 'Chief of Staff') returning id into o2;
  insert into applications (offer_id, canal, approuve_le, statut) values (o2, 'linkedin', now(), 'prete_a_envoyer') returning id into a2;
  begin
    update applications set statut = 'envoyee', date_envoi = now(), mode_envoi = 'auto' where id = a2;
    raise exception 'ÉCHEC : envoi auto LinkedIn accepté';
  exception when check_violation then null;
  end;
  update applications set statut = 'envoyee', date_envoi = now(), mode_envoi = 'manuel' where id = a2;
  raise notice 'OK 6 LinkedIn manuel uniquement';

  -- 7. Rejet avec motif obligatoire
  insert into offers (source, entreprise, intitule) values ('import_manuel', 'Acme', 'BI Analyst') returning id into o3;
  insert into applications (offer_id, canal) values (o3, 'ats') returning id into a2;
  begin
    update applications set statut = 'rejetee' where id = a2;
    raise exception 'ÉCHEC : rejet sans motif accepté';
  exception when check_violation then null;
  end;
  update applications set statut = 'rejetee', motif_rejet = 'Trop senior' where id = a2;
  raise notice 'OK 7 motif de rejet';

  -- 8. Plafond d'envois automatiques (réglé à 2 pour le test)
  update settings set value = '2' where key = 'envoi.plafond_envois_auto_jour';
  -- a1 compte déjà pour 1 envoi auto aujourd'hui
  insert into offers (source, entreprise, intitule) values ('import_manuel', 'Plafond A', 'Data Analyst') returning id into o3;
  insert into applications (offer_id, canal, approuve_le, statut, mode_envoi, date_envoi)
    values (o3, 'email', now(), 'envoyee', 'auto', now());
  insert into offers (source, entreprise, intitule) values ('import_manuel', 'Plafond B', 'Data Analyst') returning id into o3;
  begin
    insert into applications (offer_id, canal, approuve_le, statut, mode_envoi, date_envoi)
      values (o3, 'email', now(), 'envoyee', 'auto', now());
    raise exception 'ÉCHEC : plafond dépassé';
  exception when check_violation then null;
  end;
  update settings set value = '10' where key = 'envoi.plafond_envois_auto_jour';
  raise notice 'OK 8 plafond d''envois';

  -- 9. Alerte même entreprise < 30 jours
  insert into offers (source, entreprise, intitule) values ('import_manuel', 'PARFUMS CHRISTIAN DIOR', 'FP&A Analyst') returning id into o3;
  insert into applications (offer_id, canal) values (o3, 'ats') returning id into a2;
  select count(*) into n from v_alertes_meme_entreprise where application_id = a2;
  if n <> 1 then raise exception 'ÉCHEC : alerte même entreprise absente (%)', n; end if;
  raise notice 'OK 9 alerte même entreprise';

  -- 10. Vues
  perform * from v_aujourdhui;
  insert into scores (offer_id, note, recommandation, version_prompt) values (o1, 7.5, 'postuler', 'v0');
  insert into scores (offer_id, note, recommandation, version_prompt) values (o1, 8.0, 'postuler', 'v1');
  if (select note from v_offer_latest_score where offer_id = o1) <> 8.0 then
    raise exception 'ÉCHEC : dernier score incorrect';
  end if;
  raise notice 'OK 10 vues';
end $$;

\echo 'Tous les tests du socle passent.'
