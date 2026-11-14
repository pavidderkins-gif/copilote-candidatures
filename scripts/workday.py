#!/usr/bin/env python3
"""Offres récentes publiées sur les sites carrières Workday de grandes entreprises (lien direct
de l'entreprise, texte complet, date réelle), pour la Suisse, l'Australie, la France et les VIE.

  python3 scripts/workday.py --jours 2 > /tmp/workday.jsonl        # 3 le lundi
  python3 scripts/workday.py --jours 30 --entreprise "Julius Baer"   # test

Chaque ligne : entreprise, intitule, lieu, pays, zone (suisse|australie|france|vie),
date_publication, url (site de l'entreprise), source, texte, controles, exclusion
(voir scripts/qualite.py). Les offres exclues sont gardées (avec leur motif) pour le compte rendu.
Usage modéré : une pause entre deux requêtes.
"""
import argparse
import json
import re
import subprocess
import sys
import time
from datetime import date, timedelta

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lire_offre import sans_html  # noqa: E402
from qualite import analyser  # noqa: E402

# (entreprise, tenant, wd, site, zones) — sites vérifiés le 14/11/2026 (réponse 200 de l'API publique)
SITES = [
    ("Julius Baer", "juliusbaer", 3, "External", ("suisse",)),
    ("Roche", "roche", 3, "roche-ext", ("suisse", "vie")),
    ("Novartis", "novartis", 3, "Novartis_Careers", ("suisse", "vie")),
    ("Richemont", "richemont", 3, "Richemont", ("suisse", "vie")),
    ("Ferring", "ferring", 3, "Ferring", ("suisse",)),
    ("Embecta", "embecta", 1, "embectacareers", ("suisse",)),
    ("Logitech", "logitech", 5, "Logitech", ("suisse",)),
    ("Medtronic", "medtronic", 1, "MedtronicCareers", ("suisse",)),
    ("Caterpillar", "cat", 5, "CaterpillarCareers", ("suisse",)),
    ("Cargill", "cargill", 5, "Cargill", ("suisse",)),
    ("Bristol Myers Squibb", "bristolmyerssquibb", 5, "BMS", ("suisse",)),
    ("Procter & Gamble", "pg", 5, "1000", ("suisse",)),
    ("Commonwealth Bank", "cba", 3, "CommBank_Careers", ("australie",)),
    ("NAB", "nab", 3, "nab_careers", ("australie",)),
    ("Telstra", "telstra", 3, "Telstra_Careers", ("australie",)),
    ("Airbus", "ag", 3, "Airbus", ("vie", "france")),
    ("Thales", "thales", 3, "Careers", ("vie", "france")),
    ("Pernod Ricard", "pernodricard", 3, "pernod-ricard", ("vie", "france")),
    ("Sanofi", "sanofi", 3, "SanofiCareers", ("vie", "france", "suisse")),
    ("Michelin", "michelinhr", 3, "Michelin", ("vie", "france")),
    ("Valeo", "valeo", 3, "valeo_jobs", ("vie", "france")),
]
RECHERCHES = {
    "suisse": ("analyst", "graduate", "trainee", "finance", "data"),
    "australie": ("graduate", "analyst"),
    "france": ("analyst", "analyste"),
    "vie": ("VIE", "V.I.E"),
}
VILLES = {
    "suisse": r"switzerland|suisse|schweiz|gen[eè]v|geneva|lausanne|vevey|nyon|neuch[aâ]tel|fribourg|morges|rolle|"
              r"z[uü]rich|basel|b[aâ]le|zug|kaiseraugst|rotkreuz|schaffhausen|bern|lugano|tolochenaz|boudry|\bch\b",
    "australie": r"sydney|melbourne|brisbane",
    "france": r"paris|lyon|[iî]le-de-france|la d[ée]fense|blagnac|toulouse|clermont|marseille|bordeaux|lille|nanterre|gentilly|courbevoie",
}
TITRE_VIE = r"\bv\.?\s?i\.?\s?e\b|volontariat|international volunteer"
TITRE_UTILE = (r"analy|data|\bbi\b|business intelligence|financ|fp&a|controll|contr[ôo]l|planning|planner|supply|demand|"
               r"graduate|trainee|strategy|strat[ée]g|business|operations|reporting|treasury|tr[ée]sorer|pricing|insight|"
               r"commercial|procurement|achat|purchas|project|projet")
TITRE_HORS = r"nurse|medical science|scientist|chemist|technician|technicien|engineer\b(?!ing)|ingénieur|driver|sales representative|pharmacist|physician|intern\b|internship|stage|apprenti|alternan"
PAYS_EXCLUS_VIE = r"china|chine|japan|japon|korea|cor[ée]e|france\b"


def post(url: str, corps: dict, essais: int = 3):
    for i in range(essais):
        r = subprocess.run(["curl", "-s", "--max-time", "25", "-X", "POST", url, "-H", "Content-Type: application/json",
                            "-d", json.dumps(corps), "-w", "\n%{http_code}"], capture_output=True, text=True, errors="ignore").stdout
        sortie, _, code = r.rpartition("\n")
        if code == "200":
            try:
                return json.loads(sortie)
            except ValueError:
                pass
        time.sleep(3)
    return None


def get(url: str, essais: int = 3):
    for i in range(essais):
        r = subprocess.run(["curl", "-s", "--max-time", "25", url, "-w", "\n%{http_code}"], capture_output=True, text=True, errors="ignore").stdout
        sortie, _, code = r.rpartition("\n")
        if code == "200":
            try:
                return json.loads(sortie)
            except ValueError:
                pass
        time.sleep(3)
    return None


def age_jours(posted: str) -> int:
    p = (posted or "").lower()
    if "today" in p or "aujourd" in p:
        return 0
    if "yesterday" in p or "hier" in p:
        return 1
    m = re.search(r"(\d+)\+?\s*(day|jour)", p)
    return int(m.group(1)) if m else 99


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jours", type=int, default=2)
    ap.add_argument("--entreprise")
    a = ap.parse_args()
    vus, n_ok, n_exclu, erreurs = set(), 0, 0, []
    for nom, t, wd, site, zones in SITES:
        if a.entreprise and a.entreprise.lower() not in nom.lower():
            continue
        base = f"https://{t}.wd{wd}.myworkdayjobs.com"
        candidats, en_panne = {}, False
        for zone in zones:
            for terme in RECHERCHES[zone]:
                if en_panne:
                    break
                time.sleep(0.6)
                r = post(f"{base}/wday/cxs/{t}/{site}/jobs", {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": terme})
                if r is None:
                    erreurs.append(nom)
                    en_panne = True  # site indisponible ce matin : on passe au suivant
                    continue
                for jp in r.get("jobPostings", []):
                    titre, chemin, lieux = jp.get("title", ""), jp.get("externalPath", ""), jp.get("locationsText", "")
                    if not chemin or chemin in vus or age_jours(jp.get("postedOn")) > a.jours:
                        continue
                    bas = titre.lower()
                    if zone == "vie":
                        if not re.search(TITRE_VIE, bas):
                            continue
                    elif not re.search(TITRE_UTILE, bas) or re.search(TITRE_HORS, bas):
                        continue
                    # lieu : vérifié tout de suite si affiché, sinon sur la fiche (« 3 Locations »)
                    if zone in VILLES and not re.search(r"\d+ locations", lieux.lower()) and not re.search(VILLES[zone], lieux.lower()):
                        continue
                    candidats.setdefault(chemin, (zone, titre, lieux, age_jours(jp.get("postedOn"))))
        for chemin, (zone, titre, lieux, age) in candidats.items():
            time.sleep(0.6)
            d = get(f"{base}/wday/cxs/{t}/{site}{chemin}")
            if not d:
                erreurs.append(f"{nom} : fiche {titre}")
                continue
            info = d.get("jobPostingInfo", {})
            lieu = info.get("location", "") or lieux
            tous_lieux = " ".join([lieu] + list(info.get("additionalLocations") or []))
            pays = (info.get("country") or {}).get("descriptor", "")
            if zone in VILLES and not re.search(VILLES[zone], (tous_lieux + " " + pays).lower()):
                continue
            if zone == "vie" and re.search(PAYS_EXCLUS_VIE, (pays + " " + lieu).lower()) and not re.search(r"\d+ locations", lieux.lower()):
                continue
            vus.add(chemin)
            o = {
                "entreprise": nom, "intitule": info.get("title", titre), "lieu": tous_lieux.strip(), "pays": pays, "zone": zone,
                "date_publication": (date.today() - timedelta(days=age)).isoformat() if age < 99 else (info.get("startDate") or ""),
                "url": info.get("externalUrl") or f"{base}/{site}{chemin}", "source": f"workday:{t}",
                "contrat_source": info.get("timeType", ""), "texte": sans_html(info.get("jobDescription", "")),
            }
            o.update(analyser(o))
            n_exclu += bool(o["exclusion"])
            n_ok += not o["exclusion"]
            print(json.dumps(o, ensure_ascii=False), flush=True)
    erreurs = sorted(set(erreurs))
    print(f"workday : {n_ok} offre(s) à noter, {n_exclu} exclue(s) par le contrôle qualité"
          + (f" ; sans réponse : {', '.join(erreurs[:8])}" if erreurs else ""), file=sys.stderr)


if __name__ == "__main__":
    main()
