-- Bucket privé pour les PDF exacts envoyés (CV, LM, kits), pour la traçabilité.
-- Chemin conseillé : <application_id>/<type>-v<version>.pdf

insert into storage.buckets (id, name, public)
values ('documents', 'documents', false)
on conflict (id) do nothing;

create policy documents_proprietaire_lecture on storage.objects
  for select to authenticated
  using (bucket_id = 'documents');

create policy documents_proprietaire_ecriture on storage.objects
  for insert to authenticated
  with check (bucket_id = 'documents');
