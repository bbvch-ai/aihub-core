import { readdirSync, readFileSync, existsSync } from 'fs'
import path from 'path'
import matter from 'gray-matter'
import { fileURLToPath } from 'url'

const __dirname = path.dirname(fileURLToPath(import.meta.url));

export const DEFAULT_LOCALE = 'en';
export const DOCS_ROOT = path.resolve(__dirname, '../');
export const BASE_URL = 'https://docs.ai-hub.bbv.ch';

const SORT_ORDER = {
  ROOT: 0,
  CHANGELOG: 1000,
  LICENSES: 1001,
};

const extractNumericPrefix = (name) => {
  const match = name.match(/^(\d+)/);
  return match ? parseInt(match[1], 10) : Infinity;
};

const formatDirectoryName = (name) =>
  name
    .replace(/[-_]/g, ' ')
    .replace(/\b\w/g, char => char.toUpperCase());

const sortBySortOrderThenText = (a, b) => {
  if (a.sortOrder !== b.sortOrder) {
    return a.sortOrder - b.sortOrder;
  }
  return (a.text || '').localeCompare(b.text || '');
};

const readFrontmatter = (filePath) => {
  const content = readFileSync(filePath, 'utf-8');
  return matter(content).data;
};

const findLocalizedIndexFile = (dirPath, locale, isRoot = false) => {
  const candidates = [
    path.join(dirPath, `index.${locale}.md`),
    path.join(dirPath, `index.${DEFAULT_LOCALE}.md`),
  ];

  if (isRoot && locale !== DEFAULT_LOCALE) {
    candidates.pop();
  }

  const sourceFile = candidates.find(existsSync);

  return {
    sourceFile: sourceFile || null,
    frontmatter: sourceFile ? readFrontmatter(sourceFile) : {},
  };
};

const buildLocalizedLink = (basePath, locale) =>
  locale === DEFAULT_LOCALE ? basePath : `/${locale}${basePath}`;

const generateSidebarItemsRecursively = (dirPath, linkPath, locale) => {
  try {
    const entries = readdirSync(dirPath, { withFileTypes: true });

    return entries
      .filter(entry => entry.isDirectory() && !entry.name.startsWith('.'))
      .map(entry => {
        const fullPath = path.join(dirPath, entry.name);
        const itemLinkPath = `${linkPath}${entry.name}/`;
        const { sourceFile, frontmatter } = findLocalizedIndexFile(fullPath, locale);

        if (!sourceFile) {
          const subItems = generateSidebarItemsRecursively(fullPath, itemLinkPath, locale);
          return subItems.length > 0 ? subItems : null;
        }

        return {
          text: frontmatter.title || formatDirectoryName(entry.name),
          link: buildLocalizedLink(itemLinkPath, locale),
          sortOrder: extractNumericPrefix(entry.name),
          items: generateSidebarItemsRecursively(fullPath, itemLinkPath, locale),
          sourceFile,
          frontmatter,
        };
      })
      .flat()
      .filter(Boolean)
      .sort(sortBySortOrderThenText);
  } catch {
    return [];
  }
};

const createRootItem = (locale) => {
  const { sourceFile, frontmatter } = findLocalizedIndexFile(DOCS_ROOT, locale, true);

  if (!sourceFile) return null;

  return {
    text: frontmatter.hero?.name || frontmatter.title || 'Home',
    link: buildLocalizedLink('/', locale),
    sortOrder: SORT_ORDER.ROOT,
    sourceFile,
    frontmatter,
    items: [],
  };
};

const createSpecialPageItem = (fileName, displayName, sortOrder, locale) => {
  const dirPath = path.join(DOCS_ROOT, fileName);
  const { sourceFile, frontmatter } = findLocalizedIndexFile(dirPath, locale);

  if (!sourceFile) return null;

  return {
    text: displayName,
    link: buildLocalizedLink(`/${fileName}/`, locale),
    sortOrder,
    sourceFile,
    frontmatter,
    items: [],
  };
};

const generateDocsSectionItems = (locale) => {
  try {
    const docsBasePath = path.join(DOCS_ROOT, 'docs');
    const docEntries = readdirSync(docsBasePath, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory() && !dirent.name.startsWith('.'));

    return docEntries
      .map(entry => {
        const entryBasePath = path.join(docsBasePath, entry.name);
        const { sourceFile, frontmatter } = findLocalizedIndexFile(entryBasePath, locale);

        if (!sourceFile) return null;

        const entryLinkPath = `/docs/${entry.name}/`;

        return {
          text: frontmatter.title || formatDirectoryName(entry.name),
          link: buildLocalizedLink(entryLinkPath, locale),
          sortOrder: extractNumericPrefix(entry.name),
          items: generateSidebarItemsRecursively(entryBasePath, entryLinkPath, locale),
          sourceFile,
          frontmatter,
        };
      })
      .filter(Boolean);
  } catch {
    return [];
  }
};

export const generateSidebar = (locale = DEFAULT_LOCALE) => {
  const items = [
    createRootItem(locale),
    ...generateDocsSectionItems(locale),
    createSpecialPageItem('changelog', 'Changelog', SORT_ORDER.CHANGELOG, locale),
    createSpecialPageItem('licenses', 'Licenses', SORT_ORDER.LICENSES, locale),
  ];

  return items.filter(Boolean).sort(sortBySortOrderThenText);
};

export const formatSidebarForConfig = (items) =>
  items.map(({ text, link, items: subItems }) => {
    const formatted = { text, link };

    if (subItems?.length > 0) {
      formatted.items = formatSidebarForConfig(subItems);
      formatted.collapsible = true;
      formatted.collapsed = true;
    }

    return formatted;
  });