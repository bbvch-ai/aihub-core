import { withMermaid } from "vitepress-plugin-mermaid";
import { readdirSync, statSync, readFileSync } from 'fs'
import path from 'path'
import matter from 'gray-matter'

const DEFAULT_LOCALE = 'en';

/**
 * Extracts the numeric prefix from a folder/file name for sorting.
 * Examples:
 *   '1_vision' -> 1
 *   '10_chat_ui' -> 10
 *   'readme.md' -> Infinity (items without numbers sort last)
 */
function extractNumericPrefix(name: string): number {
  const match = name.match(/^(\d+)/);
  return match ? parseInt(match[1], 10) : Infinity;
}

/**
 * Creates a user-friendly title from a directory name.
 */
function formatName(name: string): string {
  return name
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

/**
 * Recursively generates sidebar items from a directory structure.
 * Supports language-specific files with suffixes like index.de.md, index.en.md
 */
function generateSidebarItems(
  dirPath: string,
  linkPath: string,
  locale: string = 'en',
): any[] {
  try {
    const entries = readdirSync(dirPath, { withFileTypes: true });
    const items = [];

    for (const entry of entries) {
      if (entry.name.startsWith('.')) {
        continue;
      }

      const fullPath = path.join(dirPath, entry.name);

      if (entry.isDirectory()) {
        const newLinkPath = locale !== 'en'
          ? `/${locale}${linkPath}${entry.name}/`
          : `${linkPath}${entry.name}/`;

        // Try locale-specific index file first, then fall back to generic index.md
        const localeIndexPath = path.join(fullPath, `index.${locale}.md`);
        const defaultIndexPath = path.join(fullPath, `index.${DEFAULT_LOCALE}.md`);

        let indexPath = defaultIndexPath;
        let hasLocaleVersion = false;
        try {
          statSync(localeIndexPath);
          indexPath = localeIndexPath;
          hasLocaleVersion = true;
        } catch (e) {
          // Fall back to default index.md
        }

        const subItems = generateSidebarItems(fullPath, `${linkPath}${entry.name}/`, locale);

        try {
          statSync(indexPath);
          const fileContent = readFileSync(indexPath, 'utf-8');
          const { data: frontmatter } = matter(fileContent);

          const sidebarItem: any = {
            text: frontmatter.title || formatName(entry.name),
            link: newLinkPath,
            sortOrder: extractNumericPrefix(entry.name),
          };

          if (subItems.length > 0) {
            sidebarItem.items = subItems;
            sidebarItem.collapsible = true;
            sidebarItem.collapsed = true;
          }

          items.push(sidebarItem);

        } catch (e) {
          if (subItems.length > 0) {
            items.push(...subItems);
          }
        }
      }
    }

    // Sort items by numeric prefix first, then alphabetically by text
    const sortedItems = items.sort((a, b) => {
      if (a.sortOrder !== b.sortOrder) {
        return a.sortOrder - b.sortOrder;
      }
      return a.text.localeCompare(b.text);
    });

    // Remove sortOrder property before returning (not needed in VitePress config)
    return sortedItems.map(({ sortOrder, ...rest }) => rest);

  } catch (e) {
    return [];
  }
}

/**
 * Generates the complete sidebar configuration for a specific locale.
 */
function generateSidebar(locale: string = 'en') {
  const docsRoot = path.resolve(__dirname, '../');
  const allTopLevelGroups = [];

  // --- Part 1: Handle special sections (Changelog, Licenses) ---
  // Note: Changelog and Licenses are always in English, no translations
  try {
    allTopLevelGroups.push({
      text: locale === 'de' ? 'Changelog' : 'Changelog',
      link: '/changelog/',
      collapsible: true,
      sortOrder: 1000,
    });

    allTopLevelGroups.push({
      text: locale === 'de' ? 'Licenses' : 'Licenses',
      link: '/licenses/',
      collapsible: true,
      sortOrder: 1001,
    });
  } catch (e) {
    console.warn(`[VitePress] Could not process special sections.`);
  }

  // --- Part 2: Handle each subdirectory in 'docs' as a separate top-level group ---
  try {
    const docsBasePath = path.join(docsRoot, 'docs');
    const docEntries = readdirSync(docsBasePath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'));

    for (const entry of docEntries) {
      const entryBasePath = path.join(docsBasePath, entry.name);

      // Try locale-specific index first
      const localeIndexPath = path.join(entryBasePath, `index.${locale}.md`);
      const defaultIndexPath = path.join(entryBasePath, `index.${DEFAULT_LOCALE}.md`);

      let entryRootIndexPath = defaultIndexPath;
      let hasLocaleVersion = false;
      try {
        statSync(localeIndexPath);
        entryRootIndexPath = localeIndexPath;
        hasLocaleVersion = true;
      } catch (e) {
        // Fall back to default
      }

      try {
        const entryFileContent = readFileSync(entryRootIndexPath, 'utf-8');
        const { data: entryFrontmatter } = matter(entryFileContent);

        const entryLink = locale !== 'en'
          ? `/${locale}/docs/${entry.name}/`
          : `/docs/${entry.name}/`;

        allTopLevelGroups.push({
          text: entryFrontmatter.title || formatName(entry.name),
          link: entryLink,
          collapsible: true,
          items: generateSidebarItems(entryBasePath, `/docs/${entry.name}/`, locale),
          sortOrder: extractNumericPrefix(entry.name),
        });
      } catch (e) {
        // This subdirectory might not have a root index.md, so we skip it.
        console.warn(`[VitePress] Skipping '${entry.name}' in 'docs'. Is docs/${entry.name}/index.${DEFAULT_LOCALE}.md or index.${locale}.md missing?`);
      }
    }
  } catch (e) {
    console.warn(`[VitePress] Could not read 'docs' directory.`);
  }

  // --- Part 3: Sort all collected groups and finalize ---
  allTopLevelGroups.sort((a, b) => {
    // Sort by numeric prefix first, then alphabetically by text
    if (a.sortOrder !== b.sortOrder) {
      return a.sortOrder - b.sortOrder;
    }
    return a.text.localeCompare(b.text);
  });

  // Remove sortOrder property before returning (not needed in VitePress config)
  return allTopLevelGroups.map(({ sortOrder, ...rest }) => rest);
}

// https://vitepress.dev/reference/site-config
export default withMermaid({
  title: "Swiss AI-Hub",
  description: "Developer focused documentation of the Swiss AI-Hub Agentic Platform",
  lastUpdated: true,
  base: '/aihub-core/',

  // Rewrites to map locale-specific files to clean URLs
  // English (.en.md) files map to root paths
  // German (.de.md) files map to /de/ paths
  rewrites: {
    ':path(.*)/index.en.md': ':path/index.md',
    'index.en.md': 'index.md',
    ':path(.*).en.md': ':path.md',
    ':path(.*)/index.de.md': 'de/:path/index.md',
    'index.de.md': 'de/index.md',
    ':path(.*).de.md': 'de/:path.md',
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
        search: {
          provider: 'local'
        },
        nav: [
          { text: 'Home', link: '/' },
          { text: 'AI-Hub Website', link: 'https://ai-hub.bbv.ch/' },
          { text: 'bbv Website', link: 'https://bbv.ch/' },
        ],
        sidebar: {
          '/': generateSidebar('en')
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
        search: {
          provider: 'local'
        },
        nav: [
          { text: 'Startseite', link: '/de/' },
          { text: 'AI-Hub Website', link: 'https://ai-hub.bbv.ch/' },
          { text: 'bbv Website', link: 'https://bbv.ch/' },
        ],
        sidebar: {
          '/de/': generateSidebar('de')
        },
        socialLinks: [
          { icon: 'github', link: 'https://github.com/bbvch-ai/aihub-core' }
        ]
      }
    }
  }
})