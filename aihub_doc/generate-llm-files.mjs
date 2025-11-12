import { writeFileSync, mkdirSync, existsSync, rmSync, readFileSync } from 'fs';
import path from 'path';
import matter from 'gray-matter';
import { generateSidebar, DEFAULT_LOCALE, DOCS_ROOT, BASE_URL } from './.vitepress/sidebar-logic.mjs';

const PUBLIC_DIR = path.resolve(DOCS_ROOT, 'public');

const TOC_INDENT = '  ';

const convertHeroToMarkdown = (frontmatter) => {
  const { hero, features } = frontmatter;
  if (!hero) return '';

  const sections = [
    `\n# ${hero.name}\n`,
    hero.text && `> ${hero.text}\n`,
    hero.tagline && `${hero.tagline}\n`,
    features && [
      '## Features\n',
      ...features.map(f => `### ${f.title}\n${f.details}\n`)
    ].join('\n'),
  ];

  return sections.filter(Boolean).join('\n');
};

const sanitizeForYaml = (value) => JSON.stringify(value || '');

const buildMarkdownUrl = (link, locale) => {
  if (link === '/' && locale === DEFAULT_LOCALE) return '/index.md';
  if (link === `/${locale}/` && locale !== DEFAULT_LOCALE) return `/${locale}/index.md`;
  return link.replace(/\/$/, '.md');
};

const createFrontmatterBlock = (url, title, description) =>
  `---\nurl: ${url}\ntitle: ${sanitizeForYaml(title)}\ndescription: ${sanitizeForYaml(description)}\n---\n`;

const createTocEntry = (text, url, description, depth) => {
  const indent = TOC_INDENT.repeat(depth - 1);
  const desc = description ? `: ${description.replace(/[\n\r"]/g, ' ').trim()}` : '';
  return `${indent}- [${text}](${url})${desc}`;
};

const processDocumentItem = (item, locale, tocDepth) => {
  const { text, link, sourceFile, frontmatter } = item;
  const mdPath = buildMarkdownUrl(link, locale);
  const fullUrl = `${BASE_URL}${mdPath}`;

  const rawContent = readFileSync(sourceFile, 'utf-8');
  const { content: strippedContent } = matter(rawContent);

  const title = frontmatter.hero?.name || text;
  const description = frontmatter.hero?.text || frontmatter.description;

  const heroMarkdown = frontmatter.hero ? convertHeroToMarkdown(frontmatter) : '';
  const frontmatterBlock = createFrontmatterBlock(fullUrl, text, description);
  const finalContent = frontmatterBlock + heroMarkdown + strippedContent;

  const outputPath = path.join(PUBLIC_DIR, mdPath);
  mkdirSync(path.dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, finalContent);

  return {
    content: finalContent,
    tocEntry: createTocEntry(title, fullUrl, description, tocDepth),
  };
};

const processSidebarItems = (items, locale, tocDepth = 1) => {
  const results = items.flatMap(item => {
    const itemResult = processDocumentItem(item, locale, tocDepth);
    const heading = item.sortOrder === 0 ? `## ${item.text}\n` : `### ${item.text}\n`;

    const subResults = item.items?.length
      ? processSidebarItems(item.items, locale, tocDepth + 1)
      : { contents: [], tocEntries: [] };

    return {
      contents: [itemResult.content, ...subResults.contents],
      tocEntries: [heading, itemResult.tocEntry, ...subResults.tocEntries, ''],
    };
  });

  return {
    contents: results.flatMap(r => r.contents),
    tocEntries: results.flatMap(r => r.tocEntries),
  };
};

const generateDocumentationSet = (locale) => {
  const tree = generateSidebar(locale);
  const rootItem = tree.find(item => item.sortOrder === 0);

  // For llms.txt (TOC): include all sections
  const { tocEntries } = processSidebarItems(tree, locale);

  // For llms-full.txt: exclude section 6 (Code Deep Dive)
  const treeWithoutSection6 = tree.filter(item => item.sortOrder !== 6);
  const { contents } = processSidebarItems(treeWithoutSection6, locale);

  const title = rootItem?.frontmatter.hero?.name || rootItem?.text || 'Documentation';
  const heroMarkdown = rootItem ? convertHeroToMarkdown(rootItem.frontmatter) : '';
  const toc = `${heroMarkdown}\n## Table of Contents\n${tocEntries.join('\n')}`;
  const fullContent = contents.join('\n\n---\n\n');

  return { toc, fullContent, title };
};

const cleanPublicDirectory = () => {
  const pathsToClean = [
    path.join(PUBLIC_DIR, 'docs'),
    path.join(PUBLIC_DIR, 'de'),
    ...['index.md', 'llms.txt', 'llms-full.txt', 'changelog.md', 'licenses.md']
      .map(file => path.join(PUBLIC_DIR, file)),
  ];

  pathsToClean.forEach(p => {
    if (existsSync(p)) {
      rmSync(p, { recursive: true, force: true });
    }
  });

  mkdirSync(path.join(PUBLIC_DIR, 'docs'), { recursive: true });
  mkdirSync(path.join(PUBLIC_DIR, 'de'), { recursive: true });
};

const writeDocumentationFiles = (locale, outputDir, docs) => {
  const dir = locale === DEFAULT_LOCALE ? PUBLIC_DIR : path.join(PUBLIC_DIR, locale);

  mkdirSync(dir, { recursive: true });
  writeFileSync(path.join(dir, 'llms.txt'), docs.toc);
  writeFileSync(path.join(dir, 'llms-full.txt'), docs.fullContent);
};

const main = () => {
  console.log('🔄 Starting LLM documentation generation...');

  cleanPublicDirectory();

  console.log('Generating English (en) files...');
  const enDocs = generateDocumentationSet('en');
  writeDocumentationFiles('en', PUBLIC_DIR, enDocs);

  console.log('Generating German (de) files...');
  const deDocs = generateDocumentationSet('de');
  writeDocumentationFiles('de', path.join(PUBLIC_DIR, 'de'), deDocs);

  console.log('🎉 LLM documentation generation complete.');
};

main();