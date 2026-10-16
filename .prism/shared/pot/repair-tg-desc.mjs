// repair-tg-desc.mjs - correct POT_T targets written as a POT_APPS DESCRIPTION instead of the app
// name (e.g. ["Agent observability",2,..] for Valence), and the derived oss-inspo "Also touches"
// text, for rows whose v (video id) is in the given stage files. Exact POT_APPS [name, desc] pairs
// only; anything else is reported, never guessed. Rewrites only the matched POT_T rows and their
// oss-inspo items, in place, keeping each row's own form.
//   node repair-tg-desc.mjs --plan <html> --stage <a.json,b.json> [--dry]
import fs from 'fs';
const argv = process.argv.slice(2);
const arg = k => { const i = argv.indexOf('--' + k); return i === -1 ? null : argv[i + 1]; };
const PLAN = arg('plan'), DRY = argv.includes('--dry');
const stages = (arg('stage') || '').split(',').filter(Boolean);
let src = fs.readFileSync(PLAN, 'utf8'); const before = src;
const grab = name => { const i = src.indexOf('const ' + name + '='); const j = src.indexOf('];', i); return JSON.parse(src.slice(i + name.length + 7, j + 1)); };
const PA = grab('POT_APPS'); const names = new Set(PA.map(p => p[0]));
const d2n = Object.fromEntries(PA.map(p => [p[1].toLowerCase(), p[0]]));
const vids = new Set(); const toolKeys = new Set();
for (const f of stages) { const d = JSON.parse(fs.readFileSync(f, 'utf8')); for (const v of d.videos) vids.add(v.id); for (const t of d.tools) toolKeys.add(t.slug.toLowerCase() + '|' + t.v); }
const fixed = [], unknown = [];
// POT_T rows are one JSON object each; find each candidate by its exact serialized text.
const potStart = src.indexOf('const POT_T=');
const potEnd = src.indexOf('}];', potStart) + 2;
let pot = src.slice(potStart, potEnd);
pot = pot.replace(/\{"n":(?:(?!\},\s*\{"n":).)*?"stage":"[a-z]+"\}/gs, row => {
  let r; try { r = JSON.parse(row); } catch { return row; }
  if (!toolKeys.has((r.slug || '').toLowerCase() + '|' + r.v)) return row;
  let changed = false;
  for (const x of r.tg) { if (!names.has(x[0])) { const n = d2n[x[0].toLowerCase()]; if (n) { fixed.push({ n: r.n, was: x[0], now: n }); x[0] = n; changed = true; } else unknown.push({ n: r.n, tg: x[0] }); } }
  return changed ? JSON.stringify(r) : row;
});
src = src.slice(0, potStart) + pot + src.slice(potEnd);
// oss-inspo detail text: "Also touches A, B." - swap descriptions for names on the rows fixed above.
const fixedNames = new Set(fixed.map(f => f.n));
let itemsFixed = 0;
src = src.replace(/\{"app":"[^"]*","item":"((?:[^"\\]|\\.)*)","type":"oss-inspo","detail":"((?:[^"\\]|\\.)*)"/g, (m, item, detail) => {
  const n = JSON.parse('"' + item + '"'); if (!fixedNames.has(n)) return m;
  const k = detail.lastIndexOf(' Also touches '); if (k < 0) return m;
  const head = detail.slice(0, k + 14), list = detail.slice(k + 14).replace(/\.$/, '');
  const out = list.split(', ').map(x => d2n[x.toLowerCase()] || x).join(', ');
  if (out === list) return m; itemsFixed++;
  return m.replace('"detail":"' + detail + '"', '"detail":"' + head + out + '."');
});
const potAfter = grab('POT_T'), potBefore = (() => { const i = before.indexOf('const POT_T='); const j = before.indexOf('}];', i); return JSON.parse(before.slice(i + 12, j + 2)); })();
const fail = [];
if (potAfter.length !== potBefore.length) fail.push('POT_T length changed');
if (Buffer.byteLength(src) - Buffer.byteLength(before) > 0 && !fixed.length) fail.push('bytes changed with no fix');
console.log(JSON.stringify({ fixed: fixed.length, itemsFixed, unknown, detail: fixed }));
if (fail.length) { console.log('REPAIR_TG_DESC_GATE_FAILED', fail); process.exit(1); }
if (!fixed.length) { console.log('REPAIR_TG_DESC_NOOP'); process.exit(0); }
if (!DRY) fs.writeFileSync(PLAN, src, 'utf8');
console.log(DRY ? 'DRY RUN' : 'wrote'); console.log('REPAIR_TG_DESC_OK');
