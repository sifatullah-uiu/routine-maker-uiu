const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname, '../index.html'), 'utf8');
const engine = source.slice(source.indexOf('function findNextNChunk('), source.indexOf('function showProgress('));
const context = vm.createContext({
  Promise, setTimeout, MAX_SEARCH_STEPS_PER_BATCH: 250000,
  olap: (a, b) => a.slot === b.slot,
  violatesDaily: rows => rows.filter(row => row.day === 1).length > 2,
  violatesDayCount: () => false
});
vm.runInContext(engine, context);

(async () => {
  const groups = Array.from({length: 3}, (_, course) =>
    Array.from({length: 9}, (_, slot) => ({course, slot, day:slot % 2})));
  const expected = [];
  for (const a of groups[0]) for (const b of groups[1]) for (const c of groups[2]) {
    const rows = [a, b, c];
    if (new Set(rows.map(r => r.slot)).size === 3 && !context.violatesDaily(rows)) expected.push(rows);
  }
  const result = await context.findNextNAsync(groups, Infinity, [], null, () => false, Infinity);
  assert.equal(result.found.length, expected.length);
  assert.ok(result.found.length > 6);
  assert.equal(result.exhausted, true);
  assert.equal(result.limitReached, false);

  // More than the old 250,000-node cap, with only one valid result at the end.
  const large = [Array.from({length: 260000}, (_, i) => ({slot:i, day:0})), [{slot:-1, day:0}]];
  context.olap = (a, b) => b.slot !== 259999;
  const full = await context.findNextNAsync(large, Infinity, [], null, () => false, Infinity);
  assert.equal(full.exhausted, true);
  assert.equal(full.found.length, 1);
  assert.ok(full.steps > 250000);

  let cancel = false;
  const cancelled = await context.findNextNAsync(large, Infinity, [], () => { cancel = true; }, () => cancel, Infinity);
  assert.equal(cancelled.cancelled, true);
  assert.equal(cancelled.exhausted, false);
  console.log(`Search checks passed: ${expected.length} exhaustive combinations, old-cap regression, cancellation.`);
})().catch(error => { console.error(error); process.exitCode = 1; });
