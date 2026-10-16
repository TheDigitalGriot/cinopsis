// land-potluck-batch.mjs - land ONE potluck-stage file into the DGS plan, roundup pattern
// (dgs-plan-update SKILL.md "Roundup landing pattern", lines 344-359), scoped to that one file.
//
//   node land-potluck-batch.mjs --plan <dgs-definitive-plan.html> --stage <potluck-stage/yt-batch-NNN.json>
//                               [--report <out.json>] [--dry]
//
// Stage file shape (yt-batch CONTEXT step 6): {batch, videos, tools, vidt, resolve, ossmeta, unresolved}.
//   videos  -> POT_VIDEOS rows (skip an id already present)
//   vidt    -> VIDT keys       (skip a key already present)
//   tools   -> POT_T rows + their derived oss-inspo ITEMS mirror (skip a slug already in POT_T:
//              one tool = one row, so an existing Gavel decision is never split into a twin)
//   resolve -> RESOLVE rows    (skip a slug already resolved)
//   ossmeta -> OSSMETA keys    (skip a key already present; never overwrite)
// Rows are written in the form the array already uses (spaced vs compact JSON, trailing comma).
// Every byte outside the five arrays + ITEMS is carried over untouched. Idempotent: a rerun adds 0.
// Gate before write: re-parse every touched array, deltas == planned adds, POT_T schema, no '</script'.
// Prints LAND_POTLUCK_BATCH_OK (or ..._NOOP) / exits 1 on any gate failure.
import fs from 'fs';

const argv = process.argv.slice(2);
const arg = (k, d = null) => { const i = argv.indexOf('--' + k); return i === -1 ? d : argv[i + 1]; };
const DRY = argv.includes('--dry');
const PLAN = arg('plan'), STAGE = arg('stage'), REPORT = arg('report');
if (!PLAN || !STAGE) { console.error('usage: land-potluck-batch.mjs --plan <html> --stage <json> [--report <json>] [--dry]'); process.exit(2); }

const raw = fs.readFileSync(PLAN);
if (raw[0] === 0xef && raw[1] === 0xbb && raw[2] === 0xbf) { console.error('plan carries a BOM - refusing'); process.exit(1); }
let src = raw.toString('utf8');
const before = src;
const st = JSON.parse(fs.readFileSync(STAGE, 'utf8'));

function bounds(s, name) {
  const re = new RegExp('(?:const|let|var)\\s+' + name + '\\s*=\\s*');
  const m = re.exec(s); if (!m) throw new Error('no ' + name);
  const from = m.index + m[0].length;
  const a = s.indexOf('[', from), b = s.indexOf('{', from);
  const i = (a < 0) ? b : (b < 0 ? a : Math.min(a, b));
  let d = 0, inS = false, q = '', esc = false;
  for (let j = i; j < s.length; j++) {
    const c = s[j];
    if (esc) { esc = false; continue; }
    if (inS) { if (c === '\\') esc = true; else if (c === q) inS = false; continue; }
    if (c === '"' || c === "'" || c === '`') { inS = true; q = c; continue; }
    if (c === '[' || c === '{') d++; else if (c === ']' || c === '}') { d--; if (d === 0) return [i, j]; }
  }
  throw new Error('unbalanced ' + name);
}
const val = (s, name) => { const [i, j] = bounds(s, name); return (0, eval)('(' + s.slice(i, j + 1) + ')'); };

// The form an array already uses, read from its last 600 bytes.
function formOf(s, name) {
  const [i, j] = bounds(s, name);
  const tail = s.slice(Math.max(i + 1, j - 600), j);
  const trimmed = tail.replace(/\s+$/, '');
  const trailingComma = trimmed.endsWith(',');
  const spaced = /"[A-Za-z_]+": /.test(tail);
  const sepNl = /\},\n\s*\{/.test(tail) || /",\n"/.test(tail);
  return { spaced, trailingComma, sep: sepNl ? ',\n' : (spaced ? ', ' : ',') };
}
const enc = (v, spaced) => spaced ? pyDump(v) : JSON.stringify(v);
function pyDump(v) {
  if (Array.isArray(v)) return '[' + v.map(pyDump).join(', ') + ']';
  if (v && typeof v === 'object') return '{' + Object.entries(v).map(([k, x]) => JSON.stringify(k) + ': ' + pyDump(x)).join(', ') + '}';
  return JSON.stringify(v);
}
const safe = t => t.replace(/<\//g, '<\\/');

function appendArray(name, rows) {
  if (!rows.length) return;
  const f = formOf(src, name);
  const [, j] = bounds(src, name);
  const body = rows.map(r => safe(enc(r, f.spaced))).join(f.sep);
  const ins = f.trailingComma ? body + ',\n' : f.sep + body;
  src = src.slice(0, j) + ins + src.slice(j);
}
function appendObject(name, obj) {
  const keys = Object.keys(obj); if (!keys.length) return;
  const f = formOf(src, name);
  const [, j] = bounds(src, name);
  const body = keys.map(k => safe(JSON.stringify(k) + (f.spaced ? ': ' : ':') + enc(obj[k], f.spaced))).join(f.sep);
  const ins = f.trailingComma ? body + ',\n' : f.sep + body;
  src = src.slice(0, j) + ins + src.slice(j);
}

// ---- plan the adds
const POT = val(src, 'POT_T'), VID = val(src, 'POT_VIDEOS'), VIDT = val(src, 'VIDT');
const RES = val(src, 'RESOLVE'), META = val(src, 'OSSMETA'), ITEMS = val(src, 'ITEMS');
const APPIDS = new Set(val(src, 'APPS').map(a => a.id));
const lc = s => (s || '').toLowerCase();
const potSlugs = new Set(POT.map(r => lc(r.slug)).filter(Boolean));
const vidIds = new Set(VID.map(v => v.id));
const resSlugs = new Set(RES.map(r => lc(r.r)).filter(Boolean));
const metaKeys = new Set(Object.keys(META).map(lc));
const appId = n => n.toLowerCase().replace(/[^a-z0-9]/g, '');

const report = { batch: st.batch, stage: STAGE, add: {}, skipped: { videos: [], tools: [], resolve: [], ossmeta: [], vidt: [] }, unknownApp: [], unresolvedLeftOpen: (st.unresolved || []).length };
const addV = [], addT = [], addI = [], addR = [], addM = {}, addVT = {};
for (const v of st.videos || []) { if (vidIds.has(v.id)) report.skipped.videos.push(v.id); else { addV.push(v); vidIds.add(v.id); } }
for (const [k, t] of Object.entries(st.vidt || {})) { if (k in VIDT || k in addVT) report.skipped.vidt.push(k); else addVT[k] = t; }
// A target written as a POT_APPS DESCRIPTION instead of its app name ("Agentic asset creation" for
// Lucid, yt-batch-013) is corrected from the exact POT_APPS [name, description] pair and recorded.
const POT_APPS = val(src, 'POT_APPS');
const appNames = new Set(POT_APPS.map(p => p[0]));
const descToName = Object.fromEntries(POT_APPS.map(p => [lc(p[1]), p[0]]));
report.tgCorrected = [];
for (const t of st.tools || []) {
  for (const x of t.tg || []) {
    if (!appNames.has(x[0]) && descToName[lc(x[0])]) { report.tgCorrected.push({ n: t.n, was: x[0], now: descToName[lc(x[0])] }); x[0] = descToName[lc(x[0])]; }
  }
}
for (const t of st.tools || []) {
  const s = lc(t.slug);
  if (!s) { report.skipped.tools.push({ n: t.n, why: 'no slug' }); continue; }
  if (potSlugs.has(s)) { report.skipped.tools.push({ n: t.n, slug: t.slug, v: t.v, why: 'slug already in POT_T' }); continue; }
  potSlugs.add(s); addT.push(t);
  const tg = (t.tg || []).slice().sort((a, b) => b[1] - a[1]);
  let app = tg.length ? appId(tg[0][0]) : 'cinopsis';
  if (!APPIDS.has(app) && app.startsWith('the') && APPIDS.has(app.slice(3))) app = app.slice(3); // "The Griot Model" -> griotmodel
  if (!APPIDS.has(app)) { report.unknownApp.push({ n: t.n, tg: tg[0] && tg[0][0], mapped: app }); }
  const secondary = tg.length > 1 ? ' Also touches ' + tg.slice(1).map(x => x[0]).join(', ') + '.' : '';
  addI.push({ app, item: t.n, type: 'oss-inspo', detail: t.b + secondary, src: t.src, status: 'idea', stage: t.stage || 'later', oss: t.n, slug: t.slug, decision: t.decision || 'undecided', role: t.role || '' });
}
for (const r of st.resolve || []) { const s = lc(r.r); if (!s || resSlugs.has(s)) report.skipped.resolve.push(r.r); else { resSlugs.add(s); addR.push(r); } }
for (const [k, m] of Object.entries(st.ossmeta || {})) { if (metaKeys.has(lc(k))) report.skipped.ossmeta.push(k); else { metaKeys.add(lc(k)); addM[k] = m; } }
report.add = { POT_VIDEOS: addV.length, VIDT: Object.keys(addVT).length, POT_T: addT.length, ossInspo: addI.length, RESOLVE: addR.length, OSSMETA: Object.keys(addM).length };

if (report.unknownApp.length) { console.error('REFUSED: strongest tg maps to an app id not in APPS', JSON.stringify(report.unknownApp)); process.exit(1); }

// ---- write into the text, in file order irrelevant (bounds re-read each time)
appendArray('POT_T', addT);
appendArray('POT_VIDEOS', addV);
appendObject('VIDT', addVT);
appendArray('RESOLVE', addR);
appendObject('OSSMETA', addM);
appendArray('ITEMS', addI);

// ---- gate
const fail = [];
const n = (s, name) => { const v = val(s, name); return Array.isArray(v) ? v.length : Object.keys(v).length; };
const exp = { POT_T: addT.length, POT_VIDEOS: addV.length, VIDT: Object.keys(addVT).length, RESOLVE: addR.length, OSSMETA: Object.keys(addM).length, ITEMS: addI.length };
const counts = {};
for (const [name, d] of Object.entries(exp)) {
  let a, b; try { a = n(before, name); b = n(src, name); } catch (e) { fail.push(name + ' unparseable after write: ' + e.message); continue; }
  counts[name] = [a, b]; if (b - a !== d) fail.push(`${name} delta ${b - a} != planned ${d}`);
}
const POT2 = val(src, 'POT_T');
const bad = POT2.filter(r => !r.n || r.cat === undefined || !Array.isArray(r.tg) || r.decision === undefined || !r.stage);
if (bad.length) fail.push('POT_T schema failures ' + bad.length);
const ossB = ITEMS.filter(x => x.type === 'oss-inspo').length, ossA = val(src, 'ITEMS').filter(x => x.type === 'oss-inspo').length;
if (ossA - ossB !== addI.length) fail.push('oss-inspo delta mismatch');
const sc = s => (s.match(/<\/script/gi) || []).length;
if (sc(src) !== sc(before)) fail.push('script close tag count changed');
// bytes outside the touched arrays are carried over: total growth == inserted text
report.counts = counts; report.bytes = [Buffer.byteLength(before), Buffer.byteLength(src)];
report.gate = fail.length ? fail : 'OK';
if (REPORT) fs.writeFileSync(REPORT, JSON.stringify(report, null, 1) + '\n', 'utf8');
console.log(JSON.stringify({ batch: st.batch, add: report.add, skipped: Object.fromEntries(Object.entries(report.skipped).map(([k, v]) => [k, v.length])), counts, gate: report.gate }));
if (fail.length) { console.log('LAND_POTLUCK_BATCH_GATE_FAILED'); process.exit(1); }
const total = Object.values(exp).reduce((a, b) => a + b, 0);
if (!total) { console.log('LAND_POTLUCK_BATCH_NOOP'); process.exit(0); }
if (DRY) { console.log('DRY RUN - nothing written'); console.log('LAND_POTLUCK_BATCH_OK'); process.exit(0); }
fs.writeFileSync(PLAN, src, { encoding: 'utf8' });
console.log('LAND_POTLUCK_BATCH_OK');
