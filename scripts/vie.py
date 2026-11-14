#!/usr/bin/env python3
"""VIE publiés récemment (finance, supply chain, data, achats), lus en entier.

Source de découverte : les listes VIE d'iagora (reprise des offres Business France et des sites
d'entreprises, avec la date de publication et le texte complet). Le lien à donner à David reste
celui de l'entreprise : utiliser ensuite `entreprise` + `intitule` pour le retrouver (Workday,
site carrières) ; à défaut, l'offre sur Business France (mon-vie-via), sinon la page iagora.

  python3 scripts/vie.py --jours 2 > /tmp/vie.jsonl        # 3 le lundi

Chaque ligne : entreprise, intitule, lieu, pays, zone="vie", date_publication, url (iagora),
source, texte, controles, exclusion (voir scripts/qualite.py).
Exclus d'office : Chine, Japon, Corée, France.
"""
import argparse
import html
import json
import re
import subprocess
import sys
import time
from datetime import date, datetime, timedelta

sys.path.insert(0, __file__.rsplit("/", 1)[0])
from lire_offre import sans_html  # noqa: E402
from qualite import analyser  # noqa: E402

CATEGORIES = ("finance", "logistique", "informatique", "achats")
MOIS = {m: i + 1 for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"))}
MOIS.update({"fév": 2, "fev": 2, "avr": 4, "mai": 5, "juin": 6, "juil": 7, "aoû": 8, "aou": 8, "déc": 12})
PAYS_EXCLUS = r"chine|china|japon|japan|cor[ée]e|korea|^france$"
INFORMATIQUE_UTILE = r"data|analy|\bbi\b|business intelligence|power bi|reporting|business analyst|finance|erp|sap"


def get(url: str) -> str:
    return subprocess.run(["curl", "-sL", "--max-time", "25", url], capture_output=True, text=True, errors="ignore").stdout


def date_publiee(texte: str):
    m = re.search(r"Publi[ée]+\s*:?\s*(\d{1,2})\s+([A-Za-zéû]{3,5})\.?\s+(\d{4})", texte)
    if not m:
        return None
    mois = MOIS.get(m.group(2).lower()[:4]) or MOIS.get(m.group(2).lower()[:3])
    return date(int(m.group(3)), mois, int(m.group(1))) if mois else None


def lignes_liste(page: str):
    for bloc in re.split(r'<div class="listings-row"', page)[1:]:
        lien = re.search(r'href="(https://www\.iagora\.com/work/fr/offre/[^"]+/(\d+))">([^<]+)</a>', bloc)
        if not lien:
            continue
        ent = re.search(r'<span class="dark bold">([^<]*)</span>\s*\|\s*([^<]*)<', bloc)
        yield {"url": lien.group(1), "id": lien.group(2), "intitule": html.unescape(lien.group(3)).strip(),
               "entreprise": html.unescape(ent.group(1)).strip() if ent else "", "lieu": html.unescape(ent.group(2)).strip() if ent else ""}


def lire_offre(url: str) -> dict:
    page = get(url)
    titre = re.search(r"<title[^>]*>(.*?)</title>", page, re.S)
    titre = html.unescape(titre.group(1)).replace("| iAgora.com", "").strip() if titre else ""
    m = re.match(r"(.*) chez (.*) - ([^-]+)$", titre)
    visible = re.sub(r"<script.*?</script>|<style.*?</style>", " ", page, flags=re.S)
    visible = sans_html(visible)
    debut = visible.find("Description du poste")
    fin = visible.find("Origine:", debut + 20)
    if fin < 0:
        fin = visible.find("Origine :", debut + 20)
    texte = visible[debut + len("Description du poste:"): fin].strip() if debut >= 0 and fin > 0 else ""
    texte = re.sub(r"\s*Voir texte complet\s*", " ", texte)
    origine = re.search(r"Origine\s*:\s*([^\n]+?)\s+Publi", visible)
    return {"entreprise": m.group(2).strip() if m else "", "pays": m.group(3).strip() if m else "", "texte": texte,
            "date": date_publiee(visible), "origine": origine.group(1).strip() if origine else ""}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--jours", type=int, default=2)
    a = ap.parse_args()
    limite = date.today() - timedelta(days=a.jours)
    vus, n_ok, n_exclu = set(), 0, 0
    for cat in CATEGORIES:
        anciens, offset = 0, 0
        while anciens < 4 and offset <= 150:
            page = get(f"https://www.iagora.com/work/fr/VIE/{cat}" + (f"?offset={offset}" if offset else ""))
            lignes = list(lignes_liste(page))
            if not lignes:
                break
            for l in lignes:
                if l["id"] in vus:
                    continue
                vus.add(l["id"])
                if cat == "informatique" and not re.search(INFORMATIQUE_UTILE, l["intitule"].lower()):
                    continue
                time.sleep(0.8)
                d = lire_offre(l["url"])
                if not d["date"] or d["date"] < limite:
                    anciens += 1
                    if anciens >= 4:
                        break
                    continue
                anciens = 0
                pays = d["pays"] or l["lieu"]
                if re.search(PAYS_EXCLUS, pays.lower().strip()):
                    continue
                o = {"entreprise": d["entreprise"] or l["entreprise"], "intitule": l["intitule"], "lieu": l["lieu"], "pays": pays,
                     "zone": "vie", "date_publication": d["date"].isoformat(), "url": l["url"], "source": f"iagora:{cat}",
                     "origine": d["origine"], "texte": d["texte"]}
                o.update(analyser(o))
                n_exclu += bool(o["exclusion"])
                n_ok += not o["exclusion"]
                print(json.dumps(o, ensure_ascii=False), flush=True)
            offset += 50
    print(f"vie : {n_ok} VIE à noter, {n_exclu} exclu(s) par le contrôle qualité (depuis le {limite:%d/%m})", file=sys.stderr)


if __name__ == "__main__":
    main()
