#!/usr/bin/env python3
"""Offres récentes de jobup.ch (Suisse romande) et jobs.ch (Suisse alémanique), avec leur
date de publication réelle et le lien direct de l'annonce.

Lit les données structurées (JSON-LD « JobPosting ») des pages de résultats publiques.
Une requête par recherche, avec une pause entre deux requêtes : usage modéré.

  python3 scripts/jobup.py --jours 2 > /tmp/jobup.jsonl            # recherches par défaut
  python3 scripts/jobup.py --jours 30 --terme "data analyst" --lieu Genève
  python3 scripts/jobup.py --detail <id>                            # lien de candidature externe
  python3 scripts/jobup.py --jours 2 --complet > /tmp/jobup.jsonl   # + texte complet et contrôle qualité

Sortie : une offre par ligne (JSON) au format attendu par scripts/offres.py.
"""
import argparse
import html
import json
import re
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

SITES = {
    "jobup": "https://www.jobup.ch/fr/emplois/?term={terme}&location={lieu}",
    "jobs": "https://www.jobs.ch/en/vacancies/?term={terme}&location={lieu}",
}
DETAIL = {
    "jobup": "https://www.jobup.ch/fr/emplois/detail/{id}/",
    "jobs": "https://www.jobs.ch/en/vacancies/detail/{id}/",
}

# (site, terme, lieu) — périmètre de profil/perimetre.yaml
RECHERCHES = [
    *[("jobup", t, l) for l in ("Genève", "Lausanne") for t in (
        "data analyst", "business analyst", "bi analyst", "financial analyst", "analyste financier",
        "fp&a", "contrôleur de gestion", "demand planner", "supply chain analyst", "business intelligence")],
    *[("jobup", t, l) for l in ("Neuchâtel", "Fribourg", "Vaud") for t in ("data analyst", "financial analyst", "business analyst")],
    *[("jobs", t, "Zürich") for t in ("junior data analyst", "junior financial analyst", "graduate finance", "junior business analyst")],
    # Entreprises cibles suivies nommément (SIG : CDD « Premier Emploi » pour les jeunes diplômés)
    ("jobup", "Services Industriels de Genève", ""), ("jobup", "premier emploi", "Genève"),
    *[("jobup", t, l) for l in ("Genève", "Lausanne") for t in ("junior", "graduate", "trainee")],
]


GENERIQUES = {"junior", "graduate", "trainee", "premier emploi"}
TITRE_UTILE = (r"analy|data|\bbi\b|business intelligence|financ|fp&a|controll|contr[ôo]l|planning|planner|supply|demand|"
               r"strategy|strat[ée]g|business|operations|reporting|treasury|tr[ée]sor|pricing|insight|achat|procurement|"
               r"graduate|trainee|programme|program|consultant|projet|project")


def get(url: str) -> str:
    r = subprocess.run(["curl", "-sL", "--max-time", "25", url], capture_output=True, text=True)
    return r.stdout


def offres_de_page(page: str, site: str):
    for bloc in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', page, re.S):
        try:
            data = json.loads(html.unescape(bloc))
        except json.JSONDecodeError:
            continue
        for obj in data if isinstance(data, list) else [data]:
            if not isinstance(obj, dict) or obj.get("@type") != "ItemList":
                continue
            for it in obj.get("itemListElement", []):
                jp = it.get("item", {})
                if jp.get("@type") != "JobPosting":
                    continue
                ident = (jp.get("identifier") or {}).get("value")
                adr = ((jp.get("jobLocation") or {}).get("address") or {})
                yield {
                    "entreprise": (jp.get("hiringOrganization") or {}).get("name", ""),
                    "intitule": jp.get("title", ""),
                    "lieu": adr.get("addressLocality", ""),
                    "pays": "Suisse",
                    "contrat_source": jp.get("employmentType", ""),
                    "date_publication": (jp.get("datePosted") or "")[:10],
                    "date_publication_iso": jp.get("datePosted", ""),
                    "url": DETAIL[site].format(id=ident) if ident else "",
                    "source": site + ".ch",
                    "source_ref": ident,
                    "extrait": (jp.get("description") or "")[:300],
                }


def lien_externe(ident: str, site: str = "jobup") -> str:
    """Lien de candidature sur le site de l'entreprise, s'il est indiqué dans l'annonce."""
    page = get(DETAIL[site].format(id=ident))
    for cle in ("externalUrl", "external_url", "applicationUrl", "application_url"):
        m = re.search(r'"%s"\s*:\s*"(https?:[^"]+)"' % cle, page)
        if m:
            return m.group(1).encode().decode("unicode_escape")
    return ""


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jours", type=float, default=2, help="ancienneté maximale de publication")
    ap.add_argument("--terme")
    ap.add_argument("--lieu", default="")
    ap.add_argument("--site", default="jobup", choices=SITES)
    ap.add_argument("--detail")
    ap.add_argument("--complet", action="store_true",
                    help="lit chaque annonce en entier et ajoute le contrôle qualité (scripts/qualite.py)")
    a = ap.parse_args()
    if a.complet:
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        from lire_offre import lire
        from qualite import analyser

    if a.detail:
        print(lien_externe(a.detail, a.site) or "(pas de lien externe : candidature via l'annonce)")
        return

    recherches = [(a.site, a.terme, a.lieu)] if a.terme else RECHERCHES
    limite = datetime.now(timezone.utc) - timedelta(days=a.jours)
    vues = set()
    for i, (site, terme, lieu) in enumerate(recherches):
        if i:
            time.sleep(1.5)
        page = get(SITES[site].format(terme=quote(terme), lieu=quote(lieu)))
        for o in offres_de_page(page, site):
            if not o["source_ref"] or o["source_ref"] in vues:
                continue
            try:
                d = datetime.fromisoformat(o["date_publication_iso"])
            except ValueError:
                continue
            if d < limite:
                continue
            # recherches génériques : ne garder que les intitulés du périmètre (data, finance, BI, supply chain…)
            if terme in GENERIQUES and not re.search(TITRE_UTILE, o["intitule"].lower()):
                continue
            vues.add(o["source_ref"])
            o["requete"] = f"{terme} @ {lieu or '-'}"
            o["zone"] = "suisse"
            if a.complet:
                time.sleep(1)
                fiche = lire(o["url"])
                o["texte"] = fiche.get("texte", "")
                if fiche.get("salaire"):
                    o["salaire"] = fiche["salaire"]
                o.update(analyser(o))
            print(json.dumps(o, ensure_ascii=False), flush=True)
    print(f"{len(vues)} offre(s) publiée(s) depuis {a.jours:g} jour(s)", file=sys.stderr)


if __name__ == "__main__":
    main()
