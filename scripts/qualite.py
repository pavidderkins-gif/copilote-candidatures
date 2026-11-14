#!/usr/bin/env python3
"""Contrôle qualité d'une offre à partir de son TEXTE COMPLET (jamais d'un extrait).

Écarte ce que David ne doit jamais voir : langue exigée autre que français ou anglais
(allemand surtout), nationalité ou résidence exigée, stage ou alternance, poste senior.
Repère aussi les années d'expérience demandées et les langues « un plus ».

  python3 scripts/qualite.py < candidats.jsonl > controles.jsonl
      chaque ligne doit contenir "texte" (description complète) et "intitule" ;
      ajoute "controles" et "exclusion" (motif, ou null si l'offre peut être notée).
  python3 scripts/qualite.py --url <lien>       # lit l'offre puis la contrôle (test rapide)

Règle : une offre sans texte complet (moins de 400 caractères) est exclue
(« texte complet non lu ») : on ne propose jamais une offre qu'on n'a pas lue.
"""
import json
import re
import sys

LANGUES = {
    "allemand": ("german", "allemand", "deutsch"),
    "néerlandais": ("dutch", "néerlandais", "neerlandais", "flemish", "flamand"),
    "italien": ("italian", "italien", "italienisch"),
    "espagnol": ("spanish", "espagnol", "spanisch"),
    "portugais": ("portuguese", "portugais"),
    "polonais": ("polish", "polonais"),
    "tchèque": ("czech", "tchèque"),
    "suédois": ("swedish", "suédois"),
    "danois": ("danish", "danois"),
    "norvégien": ("norwegian", "norvégien"),
    "finnois": ("finnish", "finnois"),
    "hongrois": ("hungarian", "hongrois"),
    "roumain": ("romanian", "roumain"),
    "turc": ("turkish", "turc"),
    "russe": ("russian", "russe"),
    "arabe": ("arabic", "arabe"),
    "mandarin": ("mandarin", "chinese", "chinois"),
    "japonais": ("japanese", "japonais"),
    "coréen": ("korean", "coréen"),
}
# Mots qui rendent une langue OBLIGATOIRE quand ils l'accompagnent
FORT = (r"fluent|fluency|fluently|native|mother tongue|excellent|very good|good|strong|solid|proficien\w*|"
        r"business[- ]level|professional[- ]level|working (?:knowledge|proficiency)|command of|"
        r"courant|courante|parfaite?|bonne|très bonne|excellente|maîtrise|maitrise|bilingue|"
        r"lu,? écrit|écrit et parlé|parlé et écrit|fliessend|fließend|verhandlungssicher|sehr gut\w*|gut\w*|"
        r"c1|c2|b2")
OBLIG = r"required|requirement|mandatory|must|essential|indispensable|obligatoire|exigée?|requise?|impératif|nécessaire|zwingend|erforderlich|vorausgesetzt"
PLUS = r"a plus|an asset|an advantage|advantageous|nice to have|beneficial|desirable|preferred|is a bonus|un plus|un atout|appréciée?|souhaitée?|serait un|von vorteil|wünschenswert|idealement|idéalement"

STOP_DE = ("und", "der", "die", "das", "mit", "für", "wir", "sie", "ihre", "ihr", "eine", "einen", "bei", "sind", "werden", "auf", "oder", "kenntnisse")
STOP_EN = ("and", "the", "with", "for", "our", "you", "your", "will", "are", "this", "skills", "experience")
STOP_FR = ("et", "les", "des", "pour", "avec", "vous", "nous", "une", "dans", "sur", "votre", "expérience")


def _fenetres(texte: str, mot: str, avant: int = 70, apres: int = 70):
    for m in re.finditer(r"\b%s\b" % re.escape(mot), texte):
        yield texte[max(0, m.start() - avant): m.end() + apres], m


def langues(texte: str) -> tuple[list, list]:
    """(langues obligatoires avec la phrase, langues « un plus »)."""
    bas = texte.lower()
    exigees, plus = [], []
    for langue, mots in LANGUES.items():
        for mot in mots:
            for fen, m in _fenetres(bas, mot):
                # « German market », « Swiss-German region » : pas une exigence de langue
                if re.search(r"\b%s[- ]+(markets?|speaking|part|region|clients?|customers?|subsidiar\w+|entit\w+|offices?|teams?|"
                             r"colleagues?|law|gaap|compan\w+|operations?|stakeholders?|sites?|headquarters|group|business|"
                             r"marché|filiale\w*|clients?|équipes?|bureaux?|partie)" % mot, fen):
                    continue
                phrase = re.sub(r"\s+", " ", fen).strip()
                if re.search(PLUS, fen):
                    plus.append((langue, phrase))
                elif re.search(r"\b(%s)\b" % FORT, fen) or re.search(r"\b(%s)\b" % OBLIG, fen):
                    exigees.append((langue, phrase))
    # Allemand exigé sous forme allemande : « Deutschkenntnisse », « Deutsch und Englisch »
    for m in re.finditer(r"deutschkenntnisse|deutsch (?:und|sowie) englisch|englisch und deutsch|"
                         r"stilsicher(?:es)? deutsch|deutsch (?:in wort und schrift|als muttersprache)", bas):
        fen = bas[max(0, m.start() - 80): m.end() + 80]
        if not re.search(PLUS, fen):
            exigees.append(("allemand", re.sub(r"\s+", " ", fen).strip()))
    ex = {}
    for l, p in exigees:
        ex.setdefault(l, p)
    pl = {l: p for l, p in plus if l not in ex}
    return list(ex.items()), list(pl.items())


def langue_du_texte(texte: str) -> str:
    mots = re.findall(r"[a-zäöüßéèàç]+", texte.lower())
    if len(mots) < 60:
        return "?"
    c = {k: sum(mots.count(w) for w in s) for k, s in (("de", STOP_DE), ("en", STOP_EN), ("fr", STOP_FR))}
    meilleur = max(c, key=c.get)
    autres = max(v for k, v in c.items() if k != meilleur)
    # langue nette seulement si elle domine clairement (évite « allemand » par défaut)
    return meilleur if c[meilleur] >= 8 and c[meilleur] > 1.5 * autres else "?"


def nationalite(texte: str) -> tuple[str, str]:
    """(bloquant, à vérifier) : nationalité, résidence ou habilitation exigée."""
    bas = texte.lower()
    bloquant = re.search(
        r"(australian|us|u\.s\.|american|swiss|canadian|uk|british|singapore|new zealand) (citizen\w*|"
        r"nationals?\b(?! (bank|science|foundation|park|museum|supercomputing|centre|center|team|league|day|fund|radio|library))|nationality)|"
        r"permanent resident\w*|citizenship (is )?(required|mandatory)|"
        r"(baseline|nv1|nv2|negative vetting) (security )?clearance|clearance \(?(baseline|nv1|nv2)|(us|u\.s\.|secret|top secret|ts/sci) clearance|"
        r"identified (role|position)|aboriginal and/or torres strait islander (applicants|people) only|first nations (graduate|identified)|"
        r"nationalité (suisse|américaine|australienne|britannique) (exigée|requise|obligatoire)|"
        r"without (the need for |requiring )?(visa )?sponsorship|no (visa )?sponsorship", bas)
    a_verifier = re.search(
        r"(full|unrestricted|valid|current) (australian )?(working|work) rights|right to work in (australia|the uk|the us)|"
        r"eligible to work in (australia|switzerland|the uk|the us)|security clearance|habilitation (défense|secret)|"
        r"permis (de travail|b|c) (valable|valide|requis|exigé)|work permit (is )?(required|valid)", bas)
    return (bloquant.group(0) if bloquant else ""), (a_verifier.group(0) if a_verifier else "")


def experience(texte: str) -> int:
    """Nombre d'années d'expérience minimum demandé (0 si rien de clair)."""
    bas = texte.lower()
    vus = []
    for m in re.finditer(r"(\d{1,2})\s*(?:\+|-|–|à|to|bis)?\s*(?:\d{1,2})?\s*(?:years?|yrs|ans|années|jahre)", bas):
        fen = bas[m.start(): m.end() + 70] + bas[max(0, m.start() - 50): m.start()]
        if re.search(r"experience|expérience|erfahrung|background", fen):
            n = int(m.group(1))
            if 0 < n < 20:
                vus.append(n)
    return min(vus) if vus else 0


def analyser(o: dict) -> dict:
    intitule = (o.get("intitule") or "").lower()
    texte = o.get("texte") or ""
    exigees, plus = langues(texte)
    bloquant, a_verifier = nationalite(texte)
    c = {
        "longueur_texte": len(texte),
        "langue_texte": langue_du_texte(texte),
        "langues_exigees": [l for l, _ in exigees],
        "langues_un_plus": [l for l, _ in plus],
        "preuve_langue": exigees[0][1][:200] if exigees else "",
        "nationalite_bloquante": bloquant,
        "droit_travail_a_verifier": a_verifier,
        "experience_min": experience(texte),
    }
    motif = None
    if len(texte) < 400:
        motif = "texte complet non lu"
    elif re.search(r"\b(stage|stagiaire|intern|internship|praktikum|praktikant|alternance|alternant|apprenti|apprentice|werkstudent|working student)\b", intitule) \
            and not re.search(r"\b(v\.?i\.?e|graduate)\b", intitule):
        motif = "stage, alternance ou apprentissage"
    elif re.search(r"\b(senior|sr\.?|lead|head of|principal|director|directeur|directrice|manager|vp)\b", intitule) \
            and not re.search(r"\b(junior|graduate|v\.?i\.?e|assistant)\b", intitule):
        motif = "poste senior ou de management"
    elif c["langue_texte"] == "de":
        motif = "offre rédigée en allemand (allemand exigé)"
    elif exigees:
        motif = f"{exigees[0][0]} exigé : « {exigees[0][1][:140]} »"
    elif bloquant:
        motif = f"nationalité, résidence ou habilitation exigée : « {bloquant} »"
    elif c["experience_min"] >= 5:
        motif = f"{c['experience_min']} ans d'expérience minimum"
    return {"controles": c, "exclusion": motif}


def main() -> None:
    if len(sys.argv) > 2 and sys.argv[1] == "--url":
        sys.path.insert(0, __file__.rsplit("/", 1)[0])
        from lire_offre import lire  # noqa: E402
        o = lire(sys.argv[2])
        o.update(analyser(o))
        o["texte"] = o.get("texte", "")[:300] + "…"
        print(json.dumps(o, ensure_ascii=False, indent=1))
        return
    for ligne in sys.stdin:
        if not ligne.strip():
            continue
        o = json.loads(ligne)
        o.update(analyser(o))
        print(json.dumps(o, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
