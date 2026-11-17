import { withMermaid } from "vitepress-plugin-mermaid";
import { copyOrDownloadAsMarkdownButtons } from 'vitepress-plugin-llms'
import { generateSidebar, formatSidebarForConfig } from './sidebar-logic.mjs';
import lightbox from "vitepress-plugin-lightbox"
import { fileURLToPath } from 'node:url'
import type { PageData, SiteConfig } from 'vitepress'

const localePrefix = (localeKey: string): string => (localeKey === 'root' ? '' : `${localeKey}/`)

const isPublished = (relativePath: string, siteConfig: SiteConfig): boolean =>
  relativePath in siteConfig.rewrites.inv || siteConfig.pages.includes(relativePath)

// Several pages (arc42, whitepaper, untranslated docs) exist in English only. The language
// switcher links to the same path in every other locale, so it needs to know which ones are missing.
const findUntranslatedLocales = (pageData: PageData, siteConfig: SiteConfig): string[] => {
  const localeKeys = Object.keys(siteConfig.site.locales)
  const currentLocaleKey =
    localeKeys.find((key) => key !== 'root' && pageData.relativePath.startsWith(localePrefix(key))) ?? 'root'
  const pathWithinLocale = pageData.relativePath.slice(localePrefix(currentLocaleKey).length)

  return localeKeys.filter(
    (key) => key !== currentLocaleKey && !isPublished(localePrefix(key) + pathWithinLocale, siteConfig)
  )
}

// https://vitepress.dev/reference/site-config
export default withMermaid({
  title: "Swiss AI-Hub",
  description: "Developer focused documentation of the Swiss AI-Hub Agentic Platform",
  lastUpdated: true,
  base: '/',
  sitemap: { hostname: 'https://docs.ai-hub.bbv.ch/' },

  rewrites: {
    ':path(.*)/index.en.md': ':path/index.md',
    'index.en.md': 'index.md',
    ':path(.*).en.md': ':path.md',
    ':path(.*)/index.de.md': 'de/:path/index.md',
    'index.de.md': 'de/index.md',
    ':path(.*).de.md': 'de/:path.md',
  },

  srcExclude: ['public/**/*.md', 'translate-prompt.md'],
  ignoreDeadLinks: true,

  transformPageData(pageData, { siteConfig }) {
    pageData.untranslatedLocales = findUntranslatedLocales(pageData, siteConfig)
  },

  vite: {
    resolve: {
      alias: [
        {
          // Replaces the default theme's internal useLangs, so the language switcher falls back to
          // the locale's home page instead of a page that does not exist in that locale.
          find: /^.*\/composables\/langs$/,
          replacement: fileURLToPath(new URL('./theme/composables/translationAwareLangs.ts', import.meta.url))
        }
      ]
    }
  },

  vue: {
    template: {
      compilerOptions: {
        // Treat <likec4-*> tags as native custom elements (registered by likec4-webcomponent.js).
        isCustomElement: (tag) => tag.startsWith('likec4-')
      }
    }
  },

  markdown: {
    config(md) {
      md.use(copyOrDownloadAsMarkdownButtons)
      md.use(lightbox, {});
    }
  },

  // Multi-language support
  locales: {
    root: {
      label: 'English',
      lang: 'en',
      themeConfig: {
        logo: '/logo.png',
        footer: {
          message: 'Built with ❤️ in Switzerland 🇨🇭',
          copyright: 'Copyright © 2025-bbv Software Services AG.'
        },
        search: { provider: 'local' },
        nav: [
          { text: 'Home', link: '/' },
          { text: 'AI-Hub Website', link: 'https://ai-hub.bbv.ch/' },
          { text: 'bbv Website', link: 'https://bbv.ch/' },
        ],
        // Use the imported functions here
        sidebar: {
          '/': formatSidebarForConfig(generateSidebar('en'))
        },
        socialLinks: [
          { icon: 'github', link: 'https://github.com/bbvch-ai/aihub-core' }
        ]
      }
    },
    de: {
      label: 'Deutsch',
      lang: 'de',
      link: '/de/',
      themeConfig: {
        logo: '/logo.png',
        footer: {
          message: 'Gebaut mit ❤️ in der Schweiz 🇨🇭',
          copyright: 'Copyright © 2025-bbv Software Services AG.'
        },
        search: { provider: 'local' },
        nav: [
          { text: 'Startseite', link: '/de/' },
          { text: 'AI-Hub Website', link: 'https://ai-hub.bbv.ch/' },
          { text: 'bbv Website', link: 'https://bbv.ch/' },
        ],
        // Use the imported functions here
        sidebar: {
          '/de/': formatSidebarForConfig(generateSidebar('de'))
        },
        socialLinks: [
          { icon: 'github', link: 'https://github.com/bbvch-ai/aihub-core' }
        ]
      }
    }
  }
})