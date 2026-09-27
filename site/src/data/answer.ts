/**
 * Short answers on topic pages.
 *
 * Each figure in an answer is written as [[…]], so one string serves three
 * readers: the page renders the figures as `.fig` (which puts them under the
 * English/Chinese figure-parity check), the FAQPage markup gets plain text, and
 * check-workbench.mjs can confirm every figure in the answer also appears in the
 * body of the same page. An answer summarises the page; it never introduces a
 * number the evidence below it does not show.
 */
export type AnswerPart = { text: string; fig: boolean };

export const answerParts = (answer: string): AnswerPart[] =>
  answer.split(/(\[\[[^\]]+\]\])/).filter(Boolean)
    .map(p => p.startsWith('[[') ? { text: p.slice(2, -2), fig: true } : { text: p, fig: false });

export const plainAnswer = (answer: string) => answer.replace(/\[\[([^\]]+)\]\]/g, '$1');
