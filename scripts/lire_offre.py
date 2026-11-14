#!/usr/bin/env python3
"""Lit une offre à partir de son lien et renvoie son texte complet et ses informations.

  python3 scripts/lire_offre.py <lien>            # JSON sur la sortie
  python3 scripts/lire_offre.py < liens.txt        # un lien par ligne -> JSONL

Ordre : flux officiel de l'outil de recrutement (Workday, Workable, Greenhouse, Lever,
SmartRecruiters), sinon fiche « JobPosting » de la page (jobup, jobs.ch, HelloWork, la plupart
des sites carrières), sinon texte visible de la page.
Champs : url, url_finale, code_http, source, intitule, entreprise, lieu, pays,
date_publication, contrat, salaire, texte (description complète, sans HTML).
"""
import html
import json
import re
import subprocess
import sys
import time


def curl(url: str, essais: int = 1):
    for i in range(essais):
        out = subprocess.run(["curl", "-sL", "--max-time", "25", "-o", "-", "-w", "\n__HTTP__%{http_code} %{url_effective}", url],
                             capture_output=True, text=True, errors="ignore").stdout
        corps, _, fin = out.rpartition("\n__HTTP__")
        code, _, finale = fin.partition(" ")
        code = int(code or 0)
        if code == 200 or code in (404, 410) or i == essais - 1:
            return code, finale.strip(), corps
        time.sleep(3)


def sans_html(s: str) -> str:
    s = re.sub(r"<(br|/p|/li|/h\d|/div)[^>]*>", "\n", s or "", flags=re.I)
    s = html.unescape(re.sub(r"<[^>]+>", " ", s))
    return re.sub(r"[ \t\r\f\v]+", " ", re.sub(r"\n\s*\n+", "\n", s)).strip()


def _base(url):
    return {"url": url, "url_finale": url, "code_http": 0, "source": "", "intitule": "", "entreprise": "", "lieu": "",
            "pays": "", "date_publication": "", "contrat": "", "salaire": "", "texte": ""}


def workday(url, o):
    m = re.match(r"https://([\w-]+)\.(wd\d+)\.myworkdayjobs\.com/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)/(job/[^?#]+)", url)
    if not m:
        return False
    t, wd, site, chemin = m.groups()
    code, _, corps = curl(f"https://{t}.{wd}.myworkdayjobs.com/wday/cxs/{t}/{site}/{chemin}", essais=3)
    o["code_http"] = code
    if code != 200:
        return True
    try:
        j = json.loads(corps)
    except ValueError:
        return True
    info = j.get("jobPostingInfo", {})
    o.update(source="workday", intitule=info.get("title", ""), entreprise=(j.get("hiringOrganization") or {}).get("name", t),
             lieu=info.get("location", ""), pays=(info.get("country") or {}).get("descriptor", ""),
             date_publication=info.get("startDate", ""), contrat=info.get("timeType", ""),
             texte=sans_html(info.get("jobDescription", "")), url_finale=info.get("externalUrl") or url)
    return True


def greenhouse(url, o):
    m = re.search(r"greenhouse\.io/(?:embed/job_app\?for=)?([\w-]+)/jobs/(\d+)", url)
    if not m:
        return False
    code, _, corps = curl(f"https://boards-api.greenhouse.io/v1/boards/{m.group(1)}/jobs/{m.group(2)}?content=true")
    o["code_http"] = code
    if code == 200:
        j = json.loads(corps)
        o.update(source="greenhouse", intitule=j.get("title", ""), entreprise=m.group(1), lieu=(j.get("location") or {}).get("name", ""),
                 date_publication=(j.get("first_published") or j.get("updated_at") or "")[:10], texte=sans_html(html.unescape(j.get("content", ""))))
    return True


def lever(url, o):
    m = re.search(r"jobs\.lever\.co/([\w-]+)/([0-9a-f-]{36})", url)
    if not m:
        return False
    code, _, corps = curl(f"https://api.lever.co/v0/postings/{m.group(1)}/{m.group(2)}")
    o["code_http"] = code
    if code == 200:
        j = json.loads(corps)
        texte = j.get("descriptionPlain", "") + "\n" + "\n".join(
            l.get("text", "") + "\n" + sans_html(l.get("content", "")) for l in j.get("lists", [])) + "\n" + j.get("additionalPlain", "")
        o.update(source="lever", intitule=j.get("text", ""), entreprise=m.group(1), lieu=(j.get("categories") or {}).get("location", ""),
                 contrat=(j.get("categories") or {}).get("commitment", ""), texte=texte.strip(),
                 date_publication=time.strftime("%Y-%m-%d", time.gmtime(j["createdAt"] / 1000)) if j.get("createdAt") else "")
    return True


def smartrecruiters(url, o):
    m = re.search(r"(?:jobs|careers)\.smartrecruiters\.com/([\w-]+)/(\d+)", url)
    if not m:
        return False
    code, _, corps = curl(f"https://api.smartrecruiters.com/v1/companies/{m.group(1)}/postings/{m.group(2)}")
    o["code_http"] = code
    if code == 200:
        j = json.loads(corps)
        sec = (j.get("jobAd") or {}).get("sections", {})
        texte = "\n".join(sans_html((sec.get(k) or {}).get("text", "")) for k in ("companyDescription", "jobDescription", "qualifications", "additionalInformation"))
        loc = j.get("location") or {}
        o.update(source="smartrecruiters", intitule=j.get("name", ""), entreprise=(j.get("company") or {}).get("name", m.group(1)),
                 lieu=loc.get("city", ""), pays=loc.get("country", ""), date_publication=(j.get("releasedDate") or "")[:10], texte=texte.strip())
    return True


def workable(url, o):
    m = re.match(r"https://apply\.workable\.com/([\w-]+)/j(?:obs/view)?/(\w+)", url)
    if not m:
        return False
    code, _, corps = curl(f"https://apply.workable.com/api/v2/accounts/{m.group(1)}/jobs/{m.group(2)}")
    o["code_http"] = code
    if code == 200:
        j = json.loads(corps)
        loc = j.get("location") or {}
        texte = "\n".join(sans_html(j.get(k, "")) for k in ("description", "requirements", "benefits"))
        o.update(source="workable", intitule=j.get("title", ""), entreprise=m.group(1), lieu=loc.get("city", ""), pays=loc.get("country", ""),
                 date_publication=(j.get("published") or "")[:10], contrat=j.get("type", ""), texte=texte.strip())
        return True
    return False  # sinon : lecture de la page


def page(url, o):
    code, finale, corps = curl(url, essais=2)
    o.update(code_http=code, url_finale=finale or url)
    if code != 200:
        return
    for bloc in re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', corps, re.S):
        try:
            data = json.loads(html.unescape(bloc).strip())
        except ValueError:
            continue
        for jp in (data if isinstance(data, list) else data.get("@graph", [data]) if isinstance(data, dict) else []):
            if isinstance(jp, dict) and jp.get("@type") == "JobPosting":
                loc = jp.get("jobLocation") or {}
                loc = loc[0] if isinstance(loc, list) and loc else loc
                adr = (loc.get("address") or {}) if isinstance(loc, dict) else {}
                sal = jp.get("baseSalary") or {}
                val = (sal.get("value") or {}) if isinstance(sal, dict) else {}
                montant = ""
                if isinstance(val, dict) and (val.get("minValue") or val.get("value")):
                    montant = f"{val.get('minValue') or val.get('value')}–{val.get('maxValue', '')} {sal.get('currency', '')} / {val.get('unitText', '')}".replace("– ", " ")
                o.update(source="jsonld", intitule=jp.get("title", ""), entreprise=(jp.get("hiringOrganization") or {}).get("name", ""),
                         lieu=adr.get("addressLocality", ""), pays=adr.get("addressCountry", "") if isinstance(adr.get("addressCountry"), str) else "",
                         date_publication=(jp.get("datePosted") or "")[:10], contrat=str(jp.get("employmentType") or ""),
                         salaire=montant, texte=sans_html(jp.get("description", "")))
                return
    titre = re.search(r"<title[^>]*>(.*?)</title>", corps, re.S | re.I)
    visible = re.sub(r"<script.*?</script>|<style.*?</style>|<nav.*?</nav>|<footer.*?</footer>|<header.*?</header>", " ", corps, flags=re.S | re.I)
    m = re.search(r'datePosted"?\s*(?:content=|:)\s*"(\d{4}-\d{2}-\d{2})', corps)
    o.update(source="page", intitule=html.unescape(titre.group(1)).strip() if titre else "", texte=sans_html(visible),
             date_publication=m.group(1) if m else "")


def lire(url: str) -> dict:
    o = _base(url.strip())
    for f in (workday, greenhouse, lever, smartrecruiters, workable):
        if f(o["url"], o):
            return o
    page(o["url"], o)
    return o


if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(json.dumps(lire(sys.argv[1]), ensure_ascii=False, indent=1))
    else:
        for l in sys.stdin:
            if l.strip():
                print(json.dumps(lire(l), ensure_ascii=False), flush=True)
                time.sleep(1)
