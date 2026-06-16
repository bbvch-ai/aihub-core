import { withMermaid } from "vitepress-plugin-mermaid";
import { copyOrDownloadAsMarkdownButtons } from 'vitepress-plugin-llms'
import { generateSidebar, formatSidebarForConfig } from './sidebar-logic.mjs';
import lightbox from "vitepress-plugin-lightbox"

// https://vitepress.dev/reference/site-config
export default withMermaid({
  title: "Swiss AI-Hub",
  description: "Developer focused documentation of the Swiss AI-Hub Agentic Platform",
  lastUpdated: true,
  base: '/',

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
        logo: './media/logo.png',
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
        logo: './media/logo.png',
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