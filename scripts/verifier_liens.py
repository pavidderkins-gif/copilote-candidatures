#!/usr/bin/env python3
"""Vérifie le lien de chaque offre active ou suivie et dit s'il marche vraiment.

  python3 scripts/verifier_liens.py <export_offres_dir> [<export_suivi_dir>] > /tmp/liens.jsonl

<export_offres_dir> : un JSON par offre (export ArtifactData `list offres` avec out_dir).
Vérifie les offres `propose` / `a_surveiller` et toutes celles que David suit.

Statuts (`lien_verifie`) :
  ok              l'offre est en ligne (annonce trouvée sur la page ou dans le flux officiel)
  protege         site officiel qui bloque les robots (403/429) : à ouvrir pour confirmer
  retire          404/410, page d'erreur, renvoi vers une liste, ou offre absente du flux
  non_verifiable  agrégateur ou page de résultats : pas un vrai lien d'offre
"""
import html
import json
import os
import re
import subprocess
import sys
import time
from datetime import date
from urllib.parse import urlparse

AGREGATEURS = ("indeed.", "glassdoor.", "jobleads.", "iagora.", "jooble.", "talent.com", "simplyhired.", "ziprecruiter.")
PAGES_RESULTATS = (r"jobup\.ch/\w+/(emplois|jobs)/\?", r"/q-[^/]*emplois", r"linkedin\.com/jobs/[^/]*-emplois", r"/jobs-SRCH_", r"/offres$")
MOTS_RETIRE = ("job ad expired", "annonce expirée", "offre n'est plus disponible", "no longer available", "this job is no longer",
               "position has been filled", "poste a été pourvu", "page not found", "page introuvable", "n'existe plus",
               "cannot be viewed at the moment", "has either been deleted", "offre a été supprimée", "n'est plus en ligne")


def curl(url: str, methode: str = "GET", donnees: str = ""):
    args = ["curl", "-sL", "--max-time", "25", "-o", "-", "-w", "\n__HTTP__%{http_code} %{url_effective}", "-X", methode]
    if donnees:
        args += ["-H", "Content-Type: application/json", "-d", donnees]
    out = subprocess.run(args + [url], capture_output=True, text=True, errors="ignore").stdout
    corps, _, fin = out.rpartition("\n__HTTP__")
    code, _, finale = fin.partition(" ")
    return int(code or 0), finale.strip(), corps


def verifier(url: str, intitule: str) -> tuple[str, str]:
    if not url:
        return "non_verifiable", "aucun lien"
    if any(a in url for a in AGREGATEURS) or any(re.search(p, url) for p in PAGES_RESULTATS):
        return "non_verifiable", "agrégateur ou page de résultats"
    host = urlparse(url).netloc

    # Workday : l'API publique renvoie 404 quand l'offre est fermée
    m = re.match(r"https://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)/(job/.+)$", url)
    if m:
        tenant, wd, site, chemin = m.groups()
        code, _, corps = curl(f"https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/{chemin}")
        if code == 200 and '"jobPostingInfo"' in corps:
            return "ok", "flux Workday officiel"
        return ("retire", f"Workday {code}") if code in (404, 410) else ("protege", f"Workday {code}")

    # Workable : l'offre doit figurer dans le flux du compte
    m = re.match(r"https://apply\.workable\.com/([\w-]+)/j(?:obs/view)?/(\w+)", url)
    if m:
        compte, code_offre = m.groups()
        code, _, corps = curl(f"https://apply.workable.com/api/v1/widget/accounts/{compte}")
        if code == 200:
            return ("ok", "flux Workable officiel") if code_offre in corps else ("retire", "absente du flux Workable")
        return "protege", f"Workable {code}"

    code, finale, corps = curl(url)
    bas = corps.lower()
    if code in (404, 410):
        return "retire", f"HTTP {code}"
    if code in (401, 403, 429, 999) or code == 0:
        return "protege", f"HTTP {code or 'sans réponse'}"
    if code >= 500:
        return "protege", f"HTTP {code}"

    # jobup.ch / jobs.ch : l'annonce doit contenir sa fiche JobPosting
    if "jobup.ch" in host or "jobs.ch" in host:
        if '"JobPosting"' in corps and "/detail/" in finale:
            return "ok", "annonce jobup/jobs.ch en ligne"
        return "retire", "annonce absente"
    # Redirection vers une liste ou une page d'erreur
    if finale.rstrip("/") != url.rstrip("/"):
        chemin_finale = urlparse(finale).path.lower()
        if any(k in chemin_finale for k in ("error", "erreur", "404", "not-found")) or chemin_finale in ("", "/", "/offres", "/jobs", "/careers"):
            return "retire", f"redirigé vers {chemin_finale or '/'}"
    # Annonce trop ancienne (page encore en ligne mais publiée il y a plus de 60 jours)
    m = re.search(r'datePosted"?\s*(?:content=|:)\s*"(\d{4}-\d{2}-\d{2})', corps)
    if m:
        age = (date.today() - date.fromisoformat(m.group(1))).days
        if age > 60:
            return "retire", f"annonce publiée le {m.group(1)}, il y a {age} jours"
    titre = re.search(r"<title[^>]*>(.*?)</title>", corps, re.S | re.I)
    titre = html.unescape(titre.group(1)).strip().lower() if titre else ""
    # Texte visible (sans scripts ni styles) : c'est là que les sites annoncent une offre fermée
    visible = re.sub(r"<script.*?</script>|<style.*?</style>", " ", corps, flags=re.S | re.I)
    visible = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", visible))).lower()
    if any(k in titre for k in MOTS_RETIRE) or any(k in visible for k in MOTS_RETIRE):
        return "retire", "la page indique que l'offre n'est plus disponible"
    mots = [w for w in re.findall(r"[a-zà-ÿ]{4,}", intitule.lower()) if w not in ("junior", "senior", "with", "pour", "dans")]
    if mots and sum(w in visible for w in mots) >= max(1, len(mots) // 2):
        return "ok", "page en ligne, intitulé retrouvé"
    return "ok", "page en ligne (intitulé non retrouvé dans la page)"


def lire(dossier: str) -> dict:
    out = {}
    if not dossier or not os.path.isdir(dossier):
        return out
    for f in os.listdir(dossier):
        if f.endswith(".json"):
            j = json.load(open(os.path.join(dossier, f)))
            out[j.get("id", f[:-5])] = j.get("data", j) | {"__version": j.get("version")}
    return out


def main() -> None:
    offres = lire(sys.argv[1])
    suivi = lire(sys.argv[2]) if len(sys.argv) > 2 else {}
    suivies = {k for k, v in suivi.items() if v.get("etape") not in (None, "nouvelle", "ecartee")}
    cibles = {k: v for k, v in offres.items() if v.get("statut") in ("propose", "a_surveiller") or k in suivies}
    for i, (oid, o) in enumerate(sorted(cibles.items(), key=lambda kv: -(kv[1].get("note") or 0))):
        if i:
            time.sleep(1)
        statut, detail = verifier(o.get("url", ""), o.get("intitule", ""))
        print(json.dumps({"id": oid, "version": o.get("__version"), "entreprise": o.get("entreprise"), "intitule": o.get("intitule"),
                          "statut_offre": o.get("statut"), "suivie": oid in suivies, "url": o.get("url"),
                          "lien_verifie": statut, "detail": detail, "lien_verifie_le": date.today().isoformat()}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
