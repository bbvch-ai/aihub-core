import { withMermaid } from "vitepress-plugin-mermaid";
import { readdirSync, statSync, readFileSync } from 'fs'
import path from 'path'
import matter from 'gray-matter'

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
 */
function generateSidebarItems(
  dirPath: string,
  linkPath: string,
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
        const newLinkPath = `${linkPath}${entry.name}/`;
        const indexPath = path.join(fullPath, 'index.md');
        const subItems = generateSidebarItems(fullPath, newLinkPath);

        try {
          statSync(indexPath);
          const fileContent = readFileSync(indexPath, 'utf-8');
          const { data: frontmatter } = matter(fileContent);

          const sidebarItem: any = {
            text: frontmatter.title || formatName(entry.name),
            link: newLinkPath,
            index: frontmatter.index,
          };

          if (subItems.length > 0) {
            sidebarItem.items = subItems;
            sidebarItem.collapsible = true;
          }

          items.push(sidebarItem);

        } catch (e) {
          if (subItems.length > 0) {
            items.push(...subItems);
          }
        }
      }
    }

    return items.sort((a, b) => {
      const aHasIndex = a.index !== undefined;
      const bHasIndex = b.index !== undefined;

      if (aHasIndex && bHasIndex) {
        return a.index !== b.index ? a.index - b.index : a.text.localeCompare(b.text);
      } else if (aHasIndex) { return -1; }
      else if (bHasIndex) { return 1; }
      else { return a.text.localeCompare(b.text); }
    });

  } catch (e) {
    return [];
  }
}

/**
 * Generates the complete sidebar configuration.
 */
function generateSidebar() {
  const docsRoot = path.resolve(__dirname, '../');
  const allTopLevelGroups = [];

  // --- Part 1: Handle 'aihub' as a single top-level group ---
  try {
    const aihubBasePath = path.join(docsRoot, 'aihub');
    const rootIndexPath = path.join(aihubBasePath, 'index.md');
    const rootFileContent = readFileSync(rootIndexPath, 'utf-8');
    const { data: rootFrontmatter } = matter(rootFileContent);

    allTopLevelGroups.push({
      text: rootFrontmatter.title || 'Technical Documentation',
      link: '/aihub/',
      collapsible: true,
      items: generateSidebarItems(aihubBasePath, '/aihub/'),
      index: rootFrontmatter.index,
    });
  } catch (e) {
    console.warn(`[VitePress] Could not process 'aihub' section. Is aihub/index.md missing?`);
  }

  // --- Part 2: Handle each subdirectory in 'docs' as a separate top-level group ---
  try {
    const docsBasePath = path.join(docsRoot, 'docs');
    const docEntries = readdirSync(docsBasePath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'));

    for (const entry of docEntries) {
      const entryBasePath = path.join(docsBasePath, entry.name);
      const entryRootIndexPath = path.join(entryBasePath, 'index.md');

      try {
        const entryFileContent = readFileSync(entryRootIndexPath, 'utf-8');
        const { data: entryFrontmatter } = matter(entryFileContent);

        allTopLevelGroups.push({
          text: entryFrontmatter.title || formatName(entry.name),
          link: `/docs/${entry.name}/`,
          collapsible: true,
          items: generateSidebarItems(entryBasePath, `/docs/${entry.name}/`),
          index: entryFrontmatter.index,
        });
      } catch (e) {
        // This subdirectory might not have a root index.md, so we skip it.
        console.warn(`[VitePress] Skipping '${entry.name}' in 'docs'. Is docs/${entry.name}/index.md missing?`);
      }
    }
  } catch (e) {
    console.warn(`[VitePress] Could not read 'docs' directory.`);
  }

  // --- Part 3: Sort all collected groups and finalize ---
  allTopLevelGroups.sort((a, b) => {
    const aHasIndex = a.index !== undefined;
    const bHasIndex = b.index !== undefined;

    if (aHasIndex && bHasIndex) {
      return a.index !== b.index ? a.index - b.index : a.text.localeCompare(b.text);
    } else if (aHasIndex) { return -1; }
    else if (bHasIndex) { return 1; }
    else { return a.text.localeCompare(b.text); }
  });

  return allTopLevelGroups.map(({ index, ...rest }) => rest);
}

// https://vitepress.dev/reference/site-config
export default withMermaid({
  title: "Swiss AI-Hub",
  description: "Developer focused documentation of the Swiss AI-Hub Agentic Platform",
  lastUpdated: true,
  themeConfig: {
    logo: './media/logo.png',
    footer: {
      message: 'Released under the Business Source License (BSL) 1.1',
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
    sidebar: generateSidebar(),
    socialLinks: [
      { icon: 'github', link: 'https://github.com/bbvch-ai/aihub-core' }
    ]
  }
})