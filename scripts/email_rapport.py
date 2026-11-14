#!/usr/bin/env python3
"""Met en forme l'email quotidien de David : court, clair, l'essentiel seulement.

  python3 scripts/email_rapport.py selection.json > /tmp/email.json
  -> {"objet": ..., "texte": ..., "html": ...} à passer tel quel à Gmail send_message
     (subject = objet, body = texte, htmlBody = html).

selection.json :
{
  "date": "2026-11-14",
  "stats": {"lues": 156, "exclues": 41, "vie_trouves": 15},
  "offres": [                      # une entrée par offre retenue, déjà notée et au lien vérifié
    {"categorie": "postuler" | "vie" | "australie" | "lvmh",
     "intitule": "...", "entreprise": "...", "lieu": "...", "pays": "...",
     "note": 8.5, "contrat": "CDI" | "CDD 12 mois" | "VIE 24 mois", "salaire": "",   # salaire si connu
     "en_bref": "ce que fait le poste, en une phrase",
     "pour_toi": "pourquoi ça colle, en une phrase",         # facultatif pour les VIE
     "a_savoir": "le point à vérifier, en une phrase",      # facultatif
     "url": "lien direct", "lien": "site Airbus" | "jobup" | "Business France" | ...,
     "date_publication": "2026-11-13", "dossier_pret": false}
  ],
  "a_faire": ["Relancer Julius Baer (envoyée le 06/11)", "..."]     # facultatif
}
"""
import html
import json
import sys
from datetime import date

TABLEAU = "https://claude.ai/artifact/QngVuEMvQQTe5yhy1Pqgsg"
JOURS = ("lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche")


def jjmm(iso: str) -> str:
    try:
        return date.fromisoformat(iso[:10]).strftime("%d/%m")
    except ValueError:
        return ""


def note(o) -> str:
    n = o.get("note")
    return f"{n:g}/10".replace(".", ",") if isinstance(n, (int, float)) else ""


def details(o) -> str:
    morceaux = [o.get("entreprise", ""), o.get("lieu") or o.get("pays", ""), o.get("contrat", ""), o.get("salaire", ""), note(o)]
    return " · ".join(m for m in morceaux if m)


def e(s) -> str:
    return html.escape(str(s or ""))


def carte_html(i, o) -> str:
    lignes = [f'<div style="font-size:16px;font-weight:600;margin:0 0 2px">{i}. <a href="{e(o["url"])}" style="color:#1a56db;text-decoration:none">{e(o["intitule"])}</a></div>',
              f'<div style="color:#555;font-size:14px;margin:0 0 6px">{e(details(o))}</div>']
    if o.get("en_bref"):
        lignes.append(f'<div style="font-size:14px;margin:0 0 3px"><b>Le poste :</b> {e(o["en_bref"])}</div>')
    if o.get("pour_toi"):
        lignes.append(f'<div style="font-size:14px;margin:0 0 3px"><b>Pour toi :</b> {e(o["pour_toi"])}</div>')
    if o.get("a_savoir"):
        lignes.append(f'<div style="font-size:14px;margin:0 0 3px;color:#92400e"><b>À savoir :</b> {e(o["a_savoir"])}</div>')
    pied = f'<a href="{e(o["url"])}" style="color:#1a56db">Voir l\'offre ({e(o.get("lien") or "lien direct")})</a>'
    if o.get("date_publication"):
        pied += f' <span style="color:#888">· publiée le {jjmm(o["date_publication"])}</span>'
    if o.get("dossier_pret"):
        pied += ' <span style="color:#047857">· dossier prêt dans le tableau de bord</span>'
    lignes.append(f'<div style="font-size:14px">{pied}</div>')
    return '<div style="margin:0 0 18px">' + "".join(lignes) + "</div>"


def carte_texte(i, o) -> str:
    l = [f"{i}. {o['intitule']}", f"   {details(o)}"]
    if o.get("en_bref"):
        l.append(f"   Le poste : {o['en_bref']}")
    if o.get("pour_toi"):
        l.append(f"   Pour toi : {o['pour_toi']}")
    if o.get("a_savoir"):
        l.append(f"   À savoir : {o['a_savoir']}")
    l.append(f"   {o['url']}")
    return "\n".join(l)


def ligne_vie_html(o) -> str:
    duree = f" · {e(o['contrat'])}" if o.get("contrat") else ""
    bref = f'<div style="color:#555;font-size:13px">{e(o["en_bref"])}</div>' if o.get("en_bref") else ""
    return (f'<li style="margin:0 0 8px;font-size:14px"><a href="{e(o["url"])}" style="color:#1a56db;text-decoration:none;font-weight:600">{e(o["intitule"])}</a>'
            f' — {e(o.get("entreprise") or "entreprise non indiquée")}, {e(o.get("lieu") or o.get("pays", ""))}{duree} · {note(o)}'
            f' <span style="color:#888">· {jjmm(o.get("date_publication", ""))}</span>{bref}</li>')


def ligne_vie_texte(o) -> str:
    duree = f" · {o['contrat']}" if o.get("contrat") else ""
    s = f"- {o['intitule']} — {o.get('entreprise') or 'entreprise non indiquée'}, {o.get('lieu') or o.get('pays', '')}{duree} · {note(o)}"
    return s + (f"\n  {o['en_bref']}" if o.get("en_bref") else "") + f"\n  {o['url']}"


def construire(sel: dict) -> dict:
    d = date.fromisoformat(sel["date"])
    offres = sel.get("offres", [])
    par = {c: sorted([o for o in offres if o.get("categorie") == c], key=lambda o: -(o.get("note") or 0))
           for c in ("postuler", "vie", "australie", "lvmh")}
    st = sel.get("stats", {})
    n_post, n_vie, n_au = len(par["postuler"]), len(par["vie"]), len(par["australie"])

    objet = f"Copilote {d:%d/%m} · " + (f"{n_post} offre{'s' * (n_post > 1)}" if n_post else "aucune offre forte")
    objet += f" · {n_vie} VIE" if n_vie else ""
    objet += f" · {n_au} Australie" if n_au else ""

    chapeau = f"{JOURS[d.weekday()].capitalize()} {d:%d/%m} · {st.get('lues', '?')} offres lues en entier"
    if st.get("exclues"):
        chapeau += f", {st['exclues']} écartées (langue, expérience, stage…)"

    H = ['<div style="font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;color:#111;max-width:620px;line-height:1.45">',
         f'<div style="color:#666;font-size:13px;margin:0 0 14px">{e(chapeau)}</div>']
    T = [chapeau, ""]

    if par["postuler"]:
        H.append(f'<h2 style="font-size:18px;margin:0 0 10px">À regarder aujourd\'hui ({n_post})</h2>')
        T += [f"À REGARDER AUJOURD'HUI ({n_post})", ""]
        for i, o in enumerate(par["postuler"], 1):
            H.append(carte_html(i, o))
            T += [carte_texte(i, o), ""]
    else:
        H.append('<p style="font-size:15px;margin:0 0 16px">Aucune nouvelle offre assez forte aujourd\'hui (CDI / CDD).</p>')
        T += ["Aucune nouvelle offre assez forte aujourd'hui (CDI / CDD).", ""]

    vie_trouves = st.get("vie_trouves", n_vie)
    titre_vie = f"VIE : {vie_trouves} nouveau{'x' * (vie_trouves > 1)}, {n_vie} pour toi"
    H.append(f'<h2 style="font-size:18px;margin:8px 0 8px">{e(titre_vie)}</h2>')
    T += [titre_vie.upper(), ""]
    if par["vie"]:
        H.append('<ul style="padding-left:18px;margin:0 0 16px">' + "".join(ligne_vie_html(o) for o in par["vie"]) + "</ul>")
        T += [ligne_vie_texte(o) for o in par["vie"]] + [""]
    else:
        H.append('<p style="font-size:14px;color:#555;margin:0 0 16px">Aucun VIE nouveau qui corresponde.</p>')
        T += ["Aucun VIE nouveau qui corresponde.", ""]

    if par["australie"]:
        H.append(f'<h2 style="font-size:18px;margin:8px 0 10px">Australie ({n_au})</h2>')
        T += [f"AUSTRALIE ({n_au})", ""]
        for i, o in enumerate(par["australie"], 1):
            H.append(carte_html(i, o))
            T += [carte_texte(i, o), ""]

    if par["lvmh"]:
        H.append('<h2 style="font-size:18px;margin:8px 0 8px">Groupe LVMH (candidature interne)</h2><ul style="padding-left:18px;margin:0 0 16px">')
        T += ["GROUPE LVMH (CANDIDATURE INTERNE)", ""]
        for o in par["lvmh"]:
            H.append(f'<li style="font-size:14px;margin:0 0 6px"><a href="{e(o["url"])}" style="color:#1a56db">{e(o["intitule"])}</a> — {e(details(o))}</li>')
            T.append(f"- {o['intitule']} — {details(o)}\n  {o['url']}")
        H.append("</ul>")
        T.append("")

    if sel.get("a_faire"):
        H.append('<h2 style="font-size:16px;margin:8px 0 6px">À faire</h2><ul style="padding-left:18px;margin:0 0 16px">'
                 + "".join(f'<li style="font-size:14px">{e(x)}</li>' for x in sel["a_faire"]) + "</ul>")
        T += ["À FAIRE"] + [f"- {x}" for x in sel["a_faire"]] + [""]

    H.append(f'<div style="font-size:14px;margin-top:12px"><a href="{TABLEAU}" style="color:#1a56db">Tableau de bord</a>'
             ' <span style="color:#888">: dossiers prêts, suivi, toutes les offres</span></div>'
             '<div style="font-size:14px;margin-top:14px">Respectueusement,<br>Copilote</div></div>')
    T += [f"Tableau de bord : {TABLEAU}", "", "Respectueusement,", "Copilote"]
    return {"objet": objet, "texte": "\n".join(T), "html": "".join(H)}


if __name__ == "__main__":
    sel = json.load(open(sys.argv[1]) if len(sys.argv) > 1 else sys.stdin)
    print(json.dumps(construire(sel), ensure_ascii=False))
