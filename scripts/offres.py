#!/usr/bin/env python3
"""Suivi des offres déjà vues (déduplication entreprise + intitulé) dans donnees/offres.csv.

  python3 scripts/offres.py filtrer  < candidates.jsonl  # n'imprime que les offres jamais vues
  python3 scripts/offres.py ajouter  < notees.jsonl      # ajoute les offres notées au CSV
  python3 scripts/offres.py hash "Entreprise" "Intitulé"

La normalisation est la même que normalize_text() côté Supabase, pour que les
empreintes restent identiques lors de la migration vers la base.
"""
import csv
import hashlib
import json
import re
import sys
from datetime import date
from pathlib import Path

CSV_PATH = Path(__file__).resolve().parent.parent / "donnees" / "offres.csv"
COLONNES = [
    "date_collecte", "dedup_hash", "entreprise", "intitule", "lieu", "pays", "contrat",
    "langue", "axe", "source", "url", "date_publication", "note", "recommandation",
    "statut", "motif", "version_prompt", "groupe_lvmh",
]

_ACCENTS = str.maketrans(
    "àâäáãåçéèêëíìîïñóòôöõúùûüýÿÀÂÄÁÃÅÇÉÈÊËÍÌÎÏÑÓÒÔÖÕÚÙÛÜÝŸ",
    "aaaaaaceeeeiiiinooooouuuuyyaaaaaaceeeeiiiinooooouuuuyy",
)


def normaliser(texte: str) -> str:
    t = (texte or "").translate(_ACCENTS).lower()
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def empreinte(entreprise: str, intitule: str) -> str:
    return hashlib.md5(f"{normaliser(entreprise)}|{normaliser(intitule)}".encode()).hexdigest()


def deja_vues() -> set[str]:
    if not CSV_PATH.exists():
        return set()
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return {ligne["dedup_hash"] for ligne in csv.DictReader(f)}


def lire_jsonl():
    for n, ligne in enumerate(sys.stdin, 1):
        ligne = ligne.strip()
        if ligne:
            try:
                yield json.loads(ligne)
            except json.JSONDecodeError as e:
                sys.exit(f"Ligne {n} illisible : {e}")


def filtrer() -> None:
    vues = deja_vues()
    for offre in lire_jsonl():
        h = empreinte(offre.get("entreprise", ""), offre.get("intitule", ""))
        if h in vues:
            continue
        vues.add(h)  # doublons à l'intérieur du même lot
        offre["dedup_hash"] = h
        print(json.dumps(offre, ensure_ascii=False))


def ajouter() -> None:
    vues = deja_vues()
    nouveau = not CSV_PATH.exists()
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    ajoutees = 0
    with CSV_PATH.open("a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=COLONNES, extrasaction="ignore", lineterminator="\n")
        if nouveau:
            w.writeheader()
        for offre in lire_jsonl():
            h = empreinte(offre.get("entreprise", ""), offre.get("intitule", ""))
            if h in vues:
                continue
            vues.add(h)
            offre["dedup_hash"] = h
            offre.setdefault("date_collecte", date.today().isoformat())
            w.writerow(offre)
            ajoutees += 1
    print(f"{ajoutees} offre(s) ajoutée(s) à {CSV_PATH.name}", file=sys.stderr)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "filtrer":
        filtrer()
    elif cmd == "ajouter":
        ajouter()
    elif cmd == "hash" and len(sys.argv) == 4:
        print(empreinte(sys.argv[2], sys.argv[3]))
    else:
        sys.exit(__doc__)
