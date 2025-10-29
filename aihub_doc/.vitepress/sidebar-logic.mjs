import { readdirSync, statSync, readFileSync, existsSync } from 'fs'
import path from 'path'
import matter from 'gray-matter'
import { fileURLToPath } from 'url'

// --- Constants ---
export const DEFAULT_LOCALE = 'en';
const __dirname = path.dirname(fileURLToPath(import.meta.url));
export const DOCS_ROOT = path.resolve(__dirname, '../'); // Path to /aihub_doc
export const BASE_URL = '/aihub-core'; // Your VitePress base

// --- Private Helpers ---

function extractNumericPrefix(name) {
  const match = name.match(/^(\d+)/);
  return match ? parseInt(match[1], 10) : Infinity;
}

function formatName(name) {
  return name
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());
}

function sortItems(a, b) {
  if (a.sortOrder !== b.sortOrder) {
    return a.sortOrder - b.sortOrder;
  }
  const aText = a.text || '';
  const bText = b.text || '';
  return aText.localeCompare(bText);
}

/**
 * Finds the correct index file (locale or default) for a directory.
 * isRoot flag handles finding files in the root (e.g., /index.en.md)
 * vs. subdirectories (e.g., /docs/foo/index.en.md).
 */
function findIndexFile(dirPath, locale, isRoot = false) {
  const filePrefix = isRoot ? 'index' : 'index'; // Root files are index.en.md, subfiles are /foo/index.en.md
  const localeIndexPath = path.join(dirPath, `${filePrefix}.${locale}.md`);
  const defaultIndexPath = path.join(dirPath, `${filePrefix}.${DEFAULT_LOCALE}.md`);

  let sourceFile = null;
  if (existsSync(localeIndexPath)) {
    sourceFile = localeIndexPath;
  } else if (existsSync(defaultIndexPath) && !isRoot) {
    sourceFile = defaultIndexPath;
  } else if (existsSync(defaultIndexPath) && isRoot && locale === DEFAULT_LOCALE) {
    sourceFile = defaultIndexPath;
  }

  if (sourceFile) {
    const fileContent = readFileSync(sourceFile, 'utf-8');
    const { data: frontmatter } = matter(fileContent);
    return { sourceFile, frontmatter };
  }

  return { sourceFile: null, frontmatter: {} };
}


/**
 * Recursively generates a rich sidebar tree from a directory structure.
 */
function generateRichSidebarItems(
  dirPath,
  linkPath,
  locale = 'en',
) {
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

        const { sourceFile, frontmatter } = findIndexFile(fullPath, locale);
        const subItems = generateRichSidebarItems(fullPath, `${linkPath}${entry.name}/`, locale);

        if (sourceFile) {
          items.push({
            text: frontmatter.title || formatName(entry.name),
            link: newLinkPath,
            sortOrder: extractNumericPrefix(entry.name),
            items: subItems,
            sourceFile: sourceFile,
            frontmatter: frontmatter,
          });
        } else if (subItems.length > 0) {
          items.push(...subItems);
        }
      }
    }
    return items.sort(sortItems);
  } catch (e) {
    return [];
  }
}

// --- Public API ---

/**
 * Generates the complete, rich sidebar data tree for a specific locale.
 */
export function generateSidebar(locale = 'en') {
  const allTopLevelGroups = [];

  // --- Part 0: Handle the ROOT index.md file ---
  const { sourceFile: rootSourceFile, frontmatter: rootFrontmatter } = findIndexFile(DOCS_ROOT, locale, true);
  const isDefaultLocale = locale === DEFAULT_LOCALE;

  if (rootSourceFile) {
    allTopLevelGroups.push({
      text: rootFrontmatter.hero?.name || rootFrontmatter.title || 'Home',
      link: isDefaultLocale ? '/' : `/${locale}/`,
      sortOrder: 0, // Ensure this is always first
      sourceFile: rootSourceFile,
      frontmatter: rootFrontmatter,
      items: [],
    });
  }

  // --- Part 1: Handle special sections (Changelog, Licenses) ---
  const changelogPath = path.join(DOCS_ROOT, 'changelog.md');
  if (existsSync(changelogPath)) {
    allTopLevelGroups.push({
      text: locale === 'de' ? 'Changelog' : 'Changelog',
      link: '/changelog/',
      sortOrder: 1000,
      sourceFile: changelogPath,
      frontmatter: matter(readFileSync(changelogPath, 'utf-8')).data,
      items: [],
    });
  }

  const licensesPath = path.join(DOCS_ROOT, 'licenses.md');
   if (existsSync(licensesPath)) {
    allTopLevelGroups.push({
      text: locale === 'de' ? 'Licenses' : 'Licenses',
      link: '/licenses/',
      sortOrder: 1001,
      sourceFile: licensesPath,
      frontmatter: matter(readFileSync(licensesPath, 'utf-8')).data,
      items: [],
    });
  }

  // --- Part 2: Handle each subdirectory in 'docs' ---
  try {
    const docsBasePath = path.join(DOCS_ROOT, 'docs');
    const docEntries = readdirSync(docsBasePath, { withFileTypes: true })
        .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'));

    for (const entry of docEntries) {
      const entryBasePath = path.join(docsBasePath, entry.name);
      const { sourceFile, frontmatter } = findIndexFile(entryBasePath, locale);

      if (sourceFile) {
        const entryLink = locale !== 'en'
          ? `/${locale}/docs/${entry.name}/`
          : `/docs/${entry.name}/`;

        allTopLevelGroups.push({
          text: frontmatter.title || formatName(entry.name),
          link: entryLink,
          sortOrder: extractNumericPrefix(entry.name),
          items: generateRichSidebarItems(entryBasePath, `/docs/${entry.name}/`, locale),
          sourceFile: sourceFile,
          frontmatter: frontmatter,
        });
      } else {
        // console.warn(`[Sidebar Logic] Skipping '${entry.name}'. Is docs/${entry.name}/index.${DEFAULT_LOCALE}.md or index.${locale}.md missing?`);
      }
    }
  } catch (e) {
    console.warn(`[Sidebar Logic] Could not read 'docs' directory.`);
  }

  // --- Part 3: Sort all collected groups and finalize ---
  return allTopLevelGroups.sort(sortItems);
}

/**
 * Recursively formats the rich tree for VitePress sidebar config.
 */
export function formatSidebarForConfig(items) {
  return items.map(({ text, link, items: subItems, ...rest }) => {
    const formattedItem = {
      text,
      link,
    };
    if (subItems && subItems.length > 0) {
      formattedItem.items = formatSidebarForConfig(subItems);
      formattedItem.collapsible = true;
      formattedItem.collapsed = true;
    }
    return formattedItem;
  });
}