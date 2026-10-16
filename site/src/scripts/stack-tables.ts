// Phones. A table with four or more columns, or a narrower one still wider
// than the screen, is restacked by CSS into one block per row (global.css,
// "Stacked tables"), so no results table scrolls sideways at phone width. In a
// block each cell carries its column's name, which this script copies from the
// table's own header into data-label. In the result tables it also marks each
// row's headline figure (data-lead) so it sits beside the row's name. The
// served HTML is unchanged. Without the script a wide table scrolls sideways as
// before, and wider screens never match the CSS.

const STACK_FROM = 4;
const phone = matchMedia('(max-width: 640px)');
const overflows = (t: HTMLTableElement) => !!t.parentElement && t.parentElement.scrollWidth > t.parentElement.clientWidth + 1;

/** The column names of a header, one per column: a grouped column joins its group's name and its own. */
function headerNames(head: HTMLTableSectionElement): string[] {
  const grid: string[][] = [];
  [...head.rows].forEach((row, r) => {
    let c = 0;
    for (const cell of row.cells) {
      while (grid[c]?.[r] !== undefined) c++;
      const copy = cell.cloneNode(true) as HTMLElement;
      copy.querySelectorAll('small, sup, .visually-hidden').forEach(x => x.remove());
      const text = (copy.textContent ?? '').replace(/\s+/g, ' ').trim();
      for (let i = 0; i < cell.colSpan; i++)
        for (let j = 0; j < cell.rowSpan; j++) (grid[c + i] ??= [])[r + j] = text;
      c += cell.colSpan;
    }
  });
  return grid.map(parts => [...new Set(parts.filter(Boolean))].join(' · '));
}

// Tables whose rows each lead with one figure: the protocol and encoder tables,
// the home table and the result groups on method and dataset pages.
const isResults = (t: HTMLTableElement) =>
  t.classList.contains('protocol-results') || t.classList.contains('fm-results') ||
  !!t.closest('.entity-group, .table-panel');

function label(t: HTMLTableElement) {
  if (t.closest('.matrix-frame, .tmap-frame')) return;
  // The home page's ablation table has no header of its own: its columns are the main table's.
  const head = t.tHead ?? (t.querySelector('#ablation-rows') ? document.querySelector('#result-rows')?.closest('table')?.tHead : null);
  if (!head) return;
  const names = headerNames(head);
  // A narrower table stays a table, unless even without its column floors it is wider than the phone.
  if (names.length < STACK_FROM) {
    delete t.dataset.stack;
    if (!phone.matches || !overflows(t)) return;
  }
  t.dataset.stack = '';
  const results = isResults(t);
  for (const body of t.tBodies) for (const tr of body.rows) {
    // A heading row spans the table: it stays a heading.
    if (tr.cells.length === 1 && tr.cells[0].colSpan > 1) { tr.dataset.group = ''; continue; }
    let c = 0, lead = false;
    [...tr.cells].forEach((cell, i) => {
      if (i > 0 && names[c]) cell.dataset.label = names[c];
      const figure = !!cell.querySelector('.metric, strong');
      if (results && !lead && i > 0 && figure) { cell.dataset.lead = ''; lead = true; }
      // A sentence-long cell takes the block's full width rather than a narrow half of it; a
      // short one ("15", "0.2 s") sits on one line after its column's name.
      const length = (cell.textContent ?? '').trim().length;
      if (i > 0 && !figure && length > 36) cell.dataset.wide = '';
      cell.toggleAttribute('data-short', i > 0 && length <= 12);
      c += cell.colSpan;
    });
  }
  // A note that every row of a column repeats word for word ("Mean across held-out participants")
  // prints once, under the first row, when stacked.
  const rows = [...t.tBodies].flatMap(b => [...b.rows]).filter(tr => !('group' in tr.dataset));
  for (let c = 1; c < names.length; c++) {
    const notes = rows.map(tr => tr.cells[c]?.querySelector(':scope > small'));
    const texts = new Set(notes.map(n => n?.textContent?.trim()));
    notes.forEach((n, i) => { if (n) n.toggleAttribute('data-repeat', i > 0 && notes.length > 2 && texts.size === 1); });
  }
}

function run() {
  const tables = [...document.querySelectorAll<HTMLTableElement>('main table')];
  tables.forEach(label);
  phone.addEventListener('change', () => tables.forEach(label));
  // The home table is rebuilt when another protocol is chosen; label its new rows.
  for (const t of tables.filter(t => t.querySelector('#result-rows, #ablation-rows'))) {
    let queued = false;
    new MutationObserver(() => {
      if (queued) return;
      queued = true;
      queueMicrotask(() => { queued = false; label(t); });
    }).observe(t, { childList: true, subtree: true, characterData: true });
  }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
else run();
