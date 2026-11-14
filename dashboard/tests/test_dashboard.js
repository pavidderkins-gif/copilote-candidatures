// Banc de test du tableau de bord : charge dashboard/index.html avec une copie des vraies
// données (export ArtifactData) et une imitation fidèle du runtime claude.ai (db, downloads),
// puis clique sur chaque fonction comme le ferait David.
//
//   node dashboard/tests/test_dashboard.js <dossier_export> [dossier_captures]
//
// <dossier_export> contient offres/, suivi/, dossiers/, rapports/, reglages/ (un JSON par document).
const fs = require("fs");
const path = require("path");
const { chromium } = require("playwright");

const exportDir = process.argv[2];
const shotsDir = process.argv[3] || "";
if (!exportDir) { console.error("usage: node test_dashboard.js <dossier_export> [captures]"); process.exit(2); }

function lireCollection(nom) {
  const dir = path.join(exportDir, nom);
  if (!fs.existsSync(dir)) return {};
  const out = {};
  for (const f of fs.readdirSync(dir).filter(f => f.endsWith(".json"))) {
    const j = JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
    out[j.id || f.replace(/\.json$/, "")] = j.data || j;
  }
  return out;
}
const DATA = {};
for (const c of ["offres", "suivi", "dossiers", "rapports", "reglages"]) DATA[c] = lireCollection(c);

// Imitation du runtime : snapshots asynchrones, écritures locales visibles d'abord avec
// hasPendingWrites, puis confirmées ; journal de toutes les écritures pour les vérifications.
const RUNTIME = `
window.__writes = []; window.__saves = [];
(function(){
  const store = ${JSON.stringify(DATA)};
  const listeners = { col: {}, doc: {} };
  const clone = o => JSON.parse(JSON.stringify(o));
  const snapDoc = (c, id, pending) => ({ id, exists: !!(store[c] && store[c][id]), data: () => store[c] && store[c][id] ? clone(store[c][id]) : undefined, metadata: { fromCache: false, hasPendingWrites: !!pending } });
  const snapCol = (c, pending) => { const docs = Object.keys(store[c] || {}).map(id => snapDoc(c, id, false)); return { docs, size: docs.length, empty: !docs.length, docChanges: () => [], metadata: { fromCache: false, hasPendingWrites: !!pending } }; };
  const emit = (c, id) => {
    (listeners.col[c] || []).forEach(fn => fn(snapCol(c, true)));
    (listeners.doc[c + "/" + id] || []).forEach(fn => fn(snapDoc(c, id, true)));
    setTimeout(() => {
      (listeners.col[c] || []).forEach(fn => fn(snapCol(c, false)));
      (listeners.doc[c + "/" + id] || []).forEach(fn => fn(snapDoc(c, id, false)));
    }, 40);
  };
  const docRef = (c, id) => ({
    id, path: c + "/" + id,
    get: async () => snapDoc(c, id),
    set: async (d) => { window.__writes.push({ op: "set", path: c + "/" + id, data: clone(d) }); (store[c] = store[c] || {})[id] = clone(d); emit(c, id); },
    update: async (d) => { if (!store[c] || !store[c][id]) throw { code: "invalid_argument" }; window.__writes.push({ op: "update", path: c + "/" + id, data: clone(d) }); Object.assign(store[c][id], clone(d)); emit(c, id); },
    delete: async () => { delete (store[c] || {})[id]; emit(c, id); },
    onSnapshot: (fn) => { (listeners.doc[c + "/" + id] = listeners.doc[c + "/" + id] || []).push(fn); setTimeout(() => fn(snapDoc(c, id)), 20); return () => {}; },
  });
  const db = {
    doc: (p) => { const [c, id] = p.split("/"); return docRef(c, id); },
    collection: (c) => ({ path: c, doc: (id) => docRef(c, id), onSnapshot: (fn) => { (listeners.col[c] = listeners.col[c] || []).push(fn); setTimeout(() => fn(snapCol(c)), 20); return () => {}; } }),
  };
  const downloads = { save: async (r) => { window.__saves.push({ filename: r.filename, size: (r.data && (r.data.size || r.data.length)) || 0, text: typeof r.data === "string" ? r.data.slice(0, 400) : "" }); return { status: "saved" }; } };
  window.claude = { use: async (n) => (n === "db" ? db : n === "downloads" ? downloads : null) };
})();`;

const page0 = fs.readFileSync(path.join(__dirname, "..", "index.html"), "utf8");
const SKEL = '<!doctype html><html><head><meta charset=utf8><meta name=viewport content="width=device-width,initial-scale=1,viewport-fit=cover"><style>:root{color-scheme:light}body{margin:0;font:14px system-ui}img{max-width:100%}[hidden]{display:none!important}</style></head><body>';
const HTML = SKEL + "<script>" + RUNTIME + "</script>" + page0 + "</body></html>";
const PDF = Buffer.from("%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n");
const server = require("http").createServer((req, res) => {
  if (req.url.startsWith("/_blob/")) { res.writeHead(200, { "Content-Type": "application/pdf" }); return res.end(PDF); }
  res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" }); res.end(HTML);
});
let BASE = "";

let ok = 0, ko = 0;
const check = (cond, label) => { if (cond) { ok++; console.log("  ✓ " + label); } else { ko++; console.log("  ✗ " + label); } };

(async () => {
  await new Promise(r => server.listen(0, "127.0.0.1", r));
  BASE = "http://127.0.0.1:" + server.address().port + "/";
  const browser = await chromium.launch();
  const ctx = await browser.newContext({ viewport: { width: 1280, height: 1000 }, permissions: ["clipboard-read", "clipboard-write"] });
  const p = await ctx.newPage();
  const errors = [];
  p.on("pageerror", e => errors.push(e.message));
  p.on("console", m => { if (m.type() === "error" && !/fonts\.g/.test(m.text())) errors.push(m.text()); });
  const writes = () => p.evaluate(() => window.__writes);
  const lastWrite = async (pathPrefix) => (await writes()).filter(w => w.path.startsWith(pathPrefix)).pop();
  const shot = async (name) => { if (shotsDir) await p.screenshot({ path: path.join(shotsDir, name + ".png"), fullPage: false }); };

  const offres = Object.entries(DATA.offres).map(([id, o]) => ({ id, ...o }));
  const rapportJour = Object.keys(DATA.rapports).sort().pop();
  const selection = offres.filter(o => o.rapport === rapportJour && o.statut === "propose" && !o.groupe_lvmh && (DATA.suivi[o.id] || {}).etape !== "ecartee");

  console.log("1. Chargement");
  await p.goto(BASE); await p.waitForTimeout(600);
  check(errors.length === 0, "aucune erreur JavaScript au chargement" + (errors.length ? " : " + errors.join(" | ") : ""));
  check(await p.locator("text=Qu'est-ce que je fais aujourd'hui ?").count() === 1, "vue Aujourd'hui affichée");
  const nbCartesSel = await p.locator("section:has(h2:text-is('À regarder')) article.offer").count();
  check(nbCartesSel === selection.length, `sélection du jour : ${nbCartesSel} carte(s) affichée(s), ${selection.length} attendue(s)`);
  check((await p.locator("#status").textContent()).includes("Dernière recherche"), "état de synchronisation affiché");
  await shot("1-aujourdhui");

  console.log("2. Boutons d'une carte");
  const cible = selection.find(o => !(DATA.suivi[o.id]) ) || selection[0];
  const carte = p.locator(`article.offer:has(button[data-open="${cible.id}"])`).first();
  await carte.locator('button[data-act="interessante"]').click(); await p.waitForTimeout(150);
  let w = await lastWrite("suivi/" + cible.id);
  check(w && w.data.etape === "interessante", `« Intéressé » enregistré (${cible.entreprise})`);
  check(await carte.locator(".chip.etape:text('Intéressante')").count() >= 1, "l'étape s'affiche sur la carte");
  await carte.locator('button[data-act="interessante"]').click(); await p.waitForTimeout(150);
  w = await lastWrite("suivi/" + cible.id);
  check(w && w.data.etape === "nouvelle", "deuxième clic : étape retirée");
  const btnDossier = carte.locator('button[data-act="dossier_demande"]');
  if (await btnDossier.count()) {
    await btnDossier.click(); await p.waitForTimeout(150);
    w = await lastWrite("suivi/" + cible.id);
    check(w && w.data.etape === "dossier_demande", "« Préparer le dossier » enregistré");
  }
  await carte.locator('button[data-act="ecarter"]').click(); await p.waitForTimeout(100);
  await p.fill(`#motif-${cible.id}`, "Test : trop loin");
  await p.locator(`form[data-ecart="${cible.id}"] button[type=submit]`).click(); await p.waitForTimeout(200);
  w = await lastWrite("suivi/" + cible.id);
  check(w && w.data.etape === "ecartee" && w.data.motif_ecart === "Test : trop loin", "« Écarter » avec motif enregistré");
  check(await p.locator(`section:has(h2:text-is('À regarder')) button[data-open="${cible.id}"]`).count() === 0, "l'offre écartée disparaît de la sélection");

  console.log("3. Kit Postuler");
  const avecDossier = offres.filter(o => DATA.dossiers[o.id] && !o.groupe_lvmh && (DATA.suivi[o.id] || {}).etape === "dossier_pret");
  check(avecDossier.length > 0, `${avecDossier.length} dossier(s) prêt(s) dans les données`);
  if (avecDossier.length) {
    const o = avecDossier.find(x => DATA.dossiers[x.id].cv_pdf_url) || avecDossier[0];
    const d = DATA.dossiers[o.id];
    await p.locator(`button[data-open="${o.id}"]`).first().click(); await p.waitForTimeout(200);
    check(await p.locator(".drawer .kit").count() === 1, `kit affiché pour ${o.entreprise}`);
    if (d.cv_pdf_url) {
      await p.locator('.drawer button[data-pdf]:not([data-nom="Portfolio-David-Perkins.pdf"])').first().click(); await p.waitForTimeout(300);
      const saves = await p.evaluate(() => window.__saves);
      check(saves.some(s => s.filename.endsWith(".pdf") && !s.filename.startsWith("Portfolio") && s.size > 0), "« Télécharger le PDF » propose le CV en PDF");
    }
    if (d.portfolio_pdf_url) {
      const btnPf = p.locator('.drawer button[data-nom="Portfolio-David-Perkins.pdf"]');
      check(await btnPf.count() === 1, "bouton « Télécharger le portfolio » présent");
      await btnPf.click(); await p.waitForTimeout(300);
      const saves = await p.evaluate(() => window.__saves);
      check(saves.some(s => s.filename === "Portfolio-David-Perkins.pdf" && s.size > 0), "« Télécharger le portfolio » propose le PDF");
    }
    if (d.lettre) {
      await p.locator('.drawer button[data-copy="lettre"]').click(); await p.waitForTimeout(150);
      const clip = await p.evaluate(() => navigator.clipboard.readText().catch(() => ""));
      check(clip.trim() === d.lettre.trim(), "« Copier la lettre » copie la lettre exacte");
    }
    const nbRep = await p.locator(".drawer .answer button[data-copy]").count();
    check(nbRep >= 5, `${nbRep} réponses de formulaire prêtes à copier`);
    await shot("3-kit");
    await p.locator('.drawer button[data-act="postulee"]').first().click(); await p.waitForTimeout(250);
    w = await lastWrite("suivi/" + o.id);
    check(w && w.data.etape === "postulee" && w.data.envoye_le, "« J'ai postulé » enregistre l'étape et la date d'envoi");
    check(await p.locator(".drawer .done").count() === 1, "le kit affiche « Envoyée » et la date de relance");
    await p.fill("#dr-note", "Test : contact Marie Dupont"); await p.locator("#dr-save").click(); await p.waitForTimeout(150);
    w = await lastWrite("suivi/" + o.id);
    check(w && w.data.note === "Test : contact Marie Dupont" && w.data.etape === "postulee", "note enregistrée sans changer l'étape");
    check(await p.locator(".drawer .timeline li").count() >= 1, "historique des étapes affiché dans le panneau");
    await p.keyboard.press("Escape"); await p.waitForTimeout(100);
    check(await p.locator(".drawer").count() === 0, "Échap ferme le panneau");
    // Relance : simuler un envoi il y a 8 jours, puis vérifier que la relance est proposée
    await p.evaluate(async (id) => { const db = await claude.use("db"); const s = (await db.doc("suivi/" + id).get()).data();
      const d = new Date(Date.now() - 8 * 86400000).toISOString(); await db.doc("suivi/" + id).set({ ...s, envoye_le: d }); }, o.id);
    await p.waitForTimeout(200);
    check(await p.locator(`text=À relancer`).count() >= 1, "relance proposée 7 jours après l'envoi");
    await p.locator(`button[data-open="${o.id}"]`).first().click(); await p.waitForTimeout(200);
    await p.locator('.drawer button[data-act="relance"]').click(); await p.waitForTimeout(250);
    w = await lastWrite("suivi/" + o.id);
    check(w && w.data.etape === "relance" && w.data.relance_le && w.data.nb_relances === 1, "« J'ai relancé » enregistre la relance et la compte");
    await p.keyboard.press("Escape"); await p.waitForTimeout(100);
  }

  console.log("4. Suivi");
  await p.goto(BASE + "#pipeline"); await p.waitForTimeout(500);
  check(await p.locator("h2:text-is('Prochaines actions')").count() === 1, "vue Suivi affichée");
  const nAct = await p.locator(".todo-item").count();
  check(nAct >= 1, `${nAct} prochaine(s) action(s) listée(s)`);
  check(await p.locator(".kpi").count() === 5, "5 indicateurs (envoyées, semaine, réponses, taux)");
  check(await p.locator(".weeks .week").count() === 8, "graphique des 8 dernières semaines");
  const sel = p.locator("select[data-move]").first();
  if (await sel.count()) {
    const id = await sel.getAttribute("data-move");
    await sel.selectOption("entretien"); await p.waitForTimeout(200);
    w = await lastWrite("suivi/" + id);
    check(w && w.data.etape === "entretien", "déplacer une carte dans le pipeline est enregistré");
  } else check(false, "au moins une carte dans le pipeline");
  const overflowPipe = await p.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
  check(!overflowPipe, "pas de débordement horizontal (Pipeline)");
  await shot("4-pipeline");

  console.log("5. Historique");
  await p.goto(BASE + "#historique"); await p.waitForTimeout(500);
  const lignes = await p.locator("#h-res tbody tr").count();
  check(lignes === offres.length, `${lignes} offres dans l'historique (${offres.length} attendues)`);
  await p.fill("#h-q", "Pictet"); await p.waitForTimeout(150);
  const filt = await p.locator("#h-res tbody tr").count();
  check(filt >= 1 && filt < lignes, `recherche « Pictet » : ${filt} ligne(s)`);
  await p.fill("#h-q", "");
  await p.locator("#h-csv").click(); await p.waitForTimeout(200);
  const saves = await p.evaluate(() => window.__saves);
  check(saves.some(s => s.filename.endsWith(".csv") && s.text.startsWith("﻿date_collecte")), "export CSV proposé au téléchargement");
  await shot("5-historique");

  console.log("6. Réglages");
  await p.goto(BASE + "#reglages"); await p.waitForTimeout(500);
  await p.fill("#cible-in", "Test Entreprise"); await p.locator("#add-cible button[type=submit]").click(); await p.waitForTimeout(200);
  w = await lastWrite("reglages/general");
  check(w && w.data.cibles.includes("Test Entreprise"), "ajout d'une entreprise cible enregistré");
  check((await p.inputValue("#c-pfr")).includes("43"), "prétentions France affichées");
  await p.fill("#c-pch", "CHF 85 000"); await p.locator("#f-candidat button[type=submit]").click(); await p.waitForTimeout(200);
  w = await lastWrite("reglages/candidat");
  check(w && w.data.pretentions_ch === "CHF 85 000" && w.data.email, "infos de candidature enregistrées sans perdre les autres champs");
  await shot("6-reglages");

  console.log("7. Téléphone et thème sombre");
  const mob = await browser.newContext({ viewport: { width: 390, height: 844 }, colorScheme: "dark", deviceScaleFactor: 1 });
  const m = await mob.newPage(); const merr = []; m.on("pageerror", e => merr.push(e.message));
  for (const v of ["", "#pipeline", "#historique", "#reglages"]) {
    await m.goto(BASE + v); await m.waitForTimeout(400);
    const of = await m.evaluate(() => document.documentElement.scrollWidth > window.innerWidth);
    check(!of, `téléphone ${v || "#aujourdhui"} : pas de débordement horizontal`);
  }
  if (shotsDir) { await m.goto(BASE + "#pipeline"); await m.waitForTimeout(400); await m.screenshot({ path: path.join(shotsDir, "7-telephone-suivi.png") }); }
  check(merr.length === 0, "aucune erreur JavaScript sur téléphone" + (merr.length ? " : " + merr.join(" | ") : ""));

  check(errors.length === 0, "aucune erreur JavaScript pendant tout le test" + (errors.length ? " : " + errors.join(" | ") : ""));
  console.log(`\n${ok} vérification(s) réussie(s), ${ko} échec(s)`);
  await browser.close(); server.close();
  process.exit(ko ? 1 : 0);
})().catch(e => { console.error(e); process.exit(1); });
