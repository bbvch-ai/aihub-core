import { writeFileSync, mkdirSync, existsSync, rmSync, readFileSync } from 'fs';
import path from 'path';
import matter from 'gray-matter';
// Correct import path, as this script is in `scripts/`
import { generateSidebar, DEFAULT_LOCALE, DOCS_ROOT, BASE_URL } from './.vitepress/sidebar-logic.mjs';

const PUBLIC_DIR = path.resolve(DOCS_ROOT, 'public');

/**
 * Converts hero frontmatter to markdown for LLMs.
 */
function heroToMarkdown(frontmatter) {
  const hero = frontmatter.hero;
  if (!hero) return '';

  let md = `\n# ${hero.name}\n\n`;
  if (hero.text) md += `> ${hero.text}\n\n`;
  if (hero.tagline) md += `${hero.tagline}\n\n`;

  if (frontmatter.features) {
    md += `## Features\n\n`;
    for (const feature of frontmatter.features) {
      md += `### ${feature.title}\n`;
      md += `${feature.details}\n\n`;
    }
  }
  return md;
}

/**
 * Formats the final llms.txt file content.
 */
function formatLlmsTxt(title, heroMd, toc) {
  // Prepend the hero markdown content before the TOC
  return `${heroMd}
## Table of Contents
${toc}
`;
}

/**
 * Recursively walks the rich sidebar tree to generate files.
 */
function walkTreeAndGenerateFiles(items, locale) {
  let fullContent = [];
  let toc = [];

  const localePrefix = locale === DEFAULT_LOCALE ? '' : `/${locale}`;
  const tocDepth = 1;

  for (const item of items) {
    // Special handling for the root 'Home' item
    if (item.sortOrder === 0) {
      toc.push(`## ${item.text}\n`); // Use main heading for root
    } else {
      toc.push(`### ${item.text}\n`);
    }

    // Process the group's root page
    const groupResult = processItem(item, locale, tocDepth);
    fullContent.push(groupResult.content);
    toc.push(groupResult.tocEntry);

    // Process children
    if (item.items && item.items.length > 0) {
      const subResult = walkSubItems(item.items, locale, tocDepth + 1);
      fullContent.push(...subResult.fullContent);
      toc.push(...subResult.toc);
    }

    toc.push(''); // Add a newline between groups
  }

  return {
    fullContent: fullContent.join('\n\n---\n\n'),
    toc: toc.join('\n')
  };
}

/**
 * Recursive helper for sub-items.
 */
function walkSubItems(items, locale, tocDepth) {
  let fullContent = [];
  let toc = [];

  for (const item of items) {
    const itemResult = processItem(item, locale, tocDepth);
    fullContent.push(itemResult.content);
    toc.push(itemResult.tocEntry);

    if (item.items && item.items.length > 0) {
      const subResult = walkSubItems(item.items, locale, tocDepth + 1);
      fullContent.push(...subResult.fullContent);
      toc.push(...subResult.toc);
    }
  }
  return { fullContent, toc };
}

/**
 * Processes a single item: reads its file, generates content,
 * writes the file to /public, and returns its TOC entry.
 */
function processItem(item, locale, tocDepth) {
  const { text, link, sourceFile, frontmatter } = item;

  // 1. Determine the final URL path for the .md file
  let mdPath;
  if (link === '/' && locale === DEFAULT_LOCALE) {
    mdPath = '/index.md';
  } else if (link === `/${locale}/` && locale !== DEFAULT_LOCALE) {
    mdPath = `/${locale}/index.md`;
  } else {
    mdPath = link.replace(/\/$/, '.md');
  }
  const fullUrl = `${BASE_URL}${mdPath}`;

  // 2. Create TOC entry
  const tocTitle = frontmatter.hero?.name || text;
  const description = frontmatter.hero?.text || frontmatter.description;
  const tocDescription = description ? `: ${description.replace(/[\n\r"]/g, ' ').trim()}` : '';

  const tocEntry = `${'  '.repeat(tocDepth - 1)}- [${tocTitle}](${fullUrl})${tocDescription}`;

  // 3. Read and strip content
  const rawContent = readFileSync(sourceFile, 'utf-8');
  let { content: strippedContent, data: rawFrontmatter } = matter(rawContent);

  // 4. Create final content with metadata
  // --- FIX for Bug 1: Quote title and description ---
  const safeTitle = JSON.stringify(text); // Use JSON.stringify for proper escaping
  const safeDescription = JSON.stringify(description || '');

  let metadata = `---
url: ${fullUrl}
title: ${safeTitle}
description: ${safeDescription}
---
`;

  // --- FIX for Bug 2: Handle Hero ---
  if (rawFrontmatter.hero) {
    strippedContent = heroToMarkdown(rawFrontmatter) + strippedContent;
  }

  const finalContent = metadata + strippedContent;

  // 5. Write the file to the public directory
  const outputPath = path.join(PUBLIC_DIR, mdPath);
  mkdirSync(path.dirname(outputPath), { recursive: true });
  writeFileSync(outputPath, finalContent);

  return { content: finalContent, tocEntry };
}

/**
 * Main script execution
 */
function main() {
  console.log('🔄 Starting LLM documentation generation...');

  // Clean relevant dirs in `public`
  const enPublicDir = path.join(PUBLIC_DIR, 'docs');
  const dePublicDir = path.join(PUBLIC_DIR, 'de');
  if (existsSync(enPublicDir)) rmSync(enPublicDir, { recursive: true, force: true });
  if (existsSync(dePublicDir)) rmSync(dePublicDir, { recursive: true, force: true });

  const rootFiles = ['index.md', 'llms.txt', 'llms-full.txt', 'changelog.md', 'licenses.md'];
  for (const file of rootFiles) {
    const filePath = path.join(PUBLIC_DIR, file);
    if (existsSync(filePath)) rmSync(filePath, { force: true });
  }

  mkdirSync(enPublicDir, { recursive: true });
  mkdirSync(dePublicDir, { recursive: true });

  // --- Generate English ---
  console.log('Generating English (en) files...');
  const enTree = generateSidebar('en');
  const enRootItem = enTree.find(item => item.sortOrder === 0);
  const enRootTitle = enRootItem.frontmatter.hero?.name || enRootItem.text;
  const enRootHeroMd = enRootItem ? heroToMarkdown(enRootItem.frontmatter) : '';
  const enResult = walkTreeAndGenerateFiles(enTree, 'en');

  writeFileSync(
    path.join(PUBLIC_DIR, 'llms.txt'),
    formatLlmsTxt(enRootTitle, enRootHeroMd, enResult.toc)
  );
  writeFileSync(
    path.join(PUBLIC_DIR, 'llms-full.txt'),
    enResult.fullContent
  );

  // --- Generate German ---
  console.log('Generating German (de) files...');
  const deTree = generateSidebar('de');
  const deRootItem = deTree.find(item => item.sortOrder === 0);
  const deRootTitle = deRootItem.frontmatter.hero?.name || deRootItem.text;
  const deRootHeroMd = deRootItem ? heroToMarkdown(deRootItem.frontmatter) : '';
  const deResult = walkTreeAndGenerateFiles(deTree, 'de');

  const deOutDir = path.join(PUBLIC_DIR, 'de');
  mkdirSync(deOutDir, { recursive: true });
  writeFileSync(
    path.join(deOutDir, 'llms.txt'),
    formatLlmsTxt(deRootTitle, deRootHeroMd, deResult.toc)
  );
  writeFileSync(
    path.join(deOutDir, 'llms-full.txt'),
    deResult.fullContent
  );

  console.log('🎉 LLM documentation generation complete.');
}

main();