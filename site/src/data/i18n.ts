/**
 * Interface copy in English and Chinese.
 *
 * What is NOT here, deliberately: dataset names, licence identifiers,
 * attribution strings, DOIs, model names and metric names. Those are citation
 * material. "CC BY 4.0" has one spelling, an author credit belongs to the person
 * who earned it, and a translated DOI is a broken link. They stay as the release
 * payload records them, in every locale.
 *
 * That is also a hard constraint rather than a preference: check-workbench.mjs
 * asserts the page-data and downloadable copies of the topic export are
 * byte-identical, and check_site_artifact.py pins the export's SHA-256 against
 * its review audit. A per-locale data layer would break the release boundary,
 * not merely look inconsistent.
 */
export const locales = ['en', 'zh'] as const;
export type Locale = (typeof locales)[number];
export const defaultLocale: Locale = 'en';

/** Written in each language's own name, which is what a switcher should show. */
export const localeNames: Record<Locale, string> = { en: 'English', zh: '中文' };

/** BCP 47 tags for `lang` and `hreflang`. */
export const htmlLang: Record<Locale, string> = { en: 'en', zh: 'zh-Hans' };

/** Prefix a path for a locale. English stays at the root. */
export function localizePath(path: string, locale: Locale): string {
  const clean = path.startsWith('/') ? path : `/${path}`;
  return locale === defaultLocale ? clean : `/${locale}${clean}`;
}

/** Recover the locale from a URL path, for the switcher and hreflang. */
export function localeFromPath(path: string): Locale {
  const segment = path.split('/').filter(Boolean)[0];
  return (locales as readonly string[]).includes(segment) ? (segment as Locale) : defaultLocale;
}

/** The same page in the other locale, used by the switcher. */
export function swapLocale(path: string, to: Locale): string {
  const current = localeFromPath(path);
  const bare = current === defaultLocale ? path : path.replace(`/${current}`, '') || '/';
  return localizePath(bare, to);
}

interface Chrome {
  stage: string;
  skipToResults: string;
  skipToEvidence: string;
  mainNav: string;
  nav: { results: string; explore: string; protocols: string; models: string;
         datasets: string; updates: string; dataUse: string };
  languageLabel: string;
  footerTagline: string;
  footerReport: string;
  footerDataUse: string;
  footerBack: string;
  /** Shown on the Chinese pages: the English text is the one that governs. */
  translationNote: string;
}

export const chrome: Record<Locale, Chrome> = {
  en: {
    stage: 'Research preview',
    skipToResults: 'Skip to results',
    skipToEvidence: 'Skip to evidence',
    mainNav: 'Main navigation',
    nav: { results: 'Results', explore: 'Explore', protocols: 'Protocols', models: 'Models',
           datasets: 'Datasets', updates: 'Updates', dataUse: 'Data use' },
    languageLabel: 'Language',
    footerTagline: 'Aggregate results. Credited sources. Research use.',
    footerReport: 'Report an issue',
    footerDataUse: 'Data use & privacy',
    footerBack: 'Back to results ↑',
    translationNote: '',
  },
  zh: {
    stage: '研究预览',
    skipToResults: '跳至结果',
    skipToEvidence: '跳至证据',
    mainNav: '主导航',
    nav: { results: '结果', explore: '专题', protocols: '协议', models: '模型',
           datasets: '数据集', updates: '动态', dataUse: '数据使用' },
    languageLabel: '语言',
    footerTagline: '聚合结果，标注来源，研究用途。',
    footerReport: '报告问题',
    footerDataUse: '数据使用与隐私',
    footerBack: '返回结果 ↑',
    translationNote: '本页为英文原文的中译。数据集名称、许可标识、署名与 DOI 保持原文，' +
                     '因为它们是引用凭据。两版有出入时以英文版为准。',
  },
};
