// The open register's filter (components/RegisterTable.astro). The server renders every row and the filter's form
// hidden; this script shows the form and, whenever a choice changes, sets or clears the `hidden` attribute on each
// row (by its data-g, data-step, data-terms and data-gap), on each group whose rows are all hidden, and on the "no row
// matches" note. It changes nothing else: no text, no class, no style. Without it every row shows.
//
// A link to a row that the filter hides (#r-…, from another row or another page) clears the choices first, so the
// row it names is on screen.

function setup(form: HTMLFormElement) {
  const ladder = form.dataset.registerFilter;
  const table = document.querySelector<HTMLTableElement>(`table[data-register-table="${ladder}"]`);
  if (!table) return;
  const empty = document.querySelector<HTMLElement>('[data-register-empty]');
  const rows = [...table.querySelectorAll<HTMLTableRowElement>('tbody > tr[data-g]')];
  const value = (name: string) => {
    const field = form.elements.namedItem(name);
    if (field instanceof HTMLInputElement) return field.checked ? field.value : '';
    return field instanceof HTMLSelectElement ? field.value : '';
  };

  function apply() {
    const g = value('g'), step = value('step'), terms = value('terms'), gap = value('gap');
    let shown = 0;
    for (const tr of rows) {
      const d = tr.dataset;
      const show = (!g || d.g === g) && (!step || d.step === step) && (!terms || d.terms === terms) && (!gap || d.gap === '1');
      tr.hidden = !show;
      if (show) shown++;
    }
    for (const body of table!.tBodies) body.hidden = ![...body.rows].some(tr => 'g' in tr.dataset && !tr.hidden);
    if (empty) empty.hidden = shown > 0;
  }

  function reveal() {
    const id = decodeURIComponent(location.hash.slice(1));
    const target = id ? document.getElementById(id) : null;
    if (!target || !table!.contains(target) || !target.closest('[hidden]')) return;
    form.reset();
    apply();
    target.scrollIntoView();
  }

  form.addEventListener('change', apply);
  form.addEventListener('submit', e => e.preventDefault());
  // A reset changes the controls after the event; read them once it has.
  form.addEventListener('reset', () => setTimeout(apply));
  window.addEventListener('hashchange', reveal);
  form.hidden = false;
  // A browser may restore the choices of an earlier visit: the rows follow them.
  apply();
  reveal();
}

function run() {
  document.querySelectorAll<HTMLFormElement>('form[data-register-filter]').forEach(setup);
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', run);
else run();
