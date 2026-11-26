import { computed } from 'vue'
import { useData } from 'vitepress'

// Drop-in replacement for the default theme's `useLangs` (wired up via a Vite alias in config.mts).
// It differs only in one point: a locale listed in the page's `untranslatedLocales` (set by
// transformPageData) links to that locale's home page instead of a page that does not exist.

const localeHomeLink = (localeKey: string, link: string | undefined): string =>
  link || (localeKey === 'root' ? '/' : `/${localeKey}/`)

const correspondingPageLink = (localeLink: string, pathWithinLocale: string, addHtmlExtension: boolean): string => {
  const path = pathWithinLocale.replace(/(^|\/)index\.md$/, '$1').replace(/\.md$/, addHtmlExtension ? '.html' : '')
  return localeLink.replace(/\/$/, '') + (path.startsWith('/') ? path : `/${path}`)
}

export function useLangs({ correspondingLink = false } = {}) {
  const { site, localeIndex, page, theme, hash } = useData()

  const currentLang = computed(() => ({
    label: site.value.locales[localeIndex.value]?.label,
    link: localeHomeLink(localeIndex.value, site.value.locales[localeIndex.value]?.link),
  }))

  const localeLinks = computed(() =>
    Object.entries(site.value.locales).flatMap(([key, value]) => {
      if (currentLang.value.label === value.label) return []

      const homeLink = localeHomeLink(key, value.link)
      const untranslated = ((page.value as { untranslatedLocales?: string[] }).untranslatedLocales ?? []).includes(key)
      if (untranslated) return { text: value.label, link: homeLink, lang: value.lang, dir: value.dir }

      const link =
        (theme.value.i18nRouting !== false && correspondingLink
          ? correspondingPageLink(
              homeLink,
              page.value.relativePath.slice(currentLang.value.link.length - 1),
              !site.value.cleanUrls
            )
          : homeLink) + hash.value

      return { text: value.label, link, lang: value.lang, dir: value.dir }
    })
  )

  return { localeLinks, currentLang }
}
