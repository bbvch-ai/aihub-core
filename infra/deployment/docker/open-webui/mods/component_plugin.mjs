import { readFileSync, realpathSync } from 'node:fs';
import path from 'node:path';
import { parse as parseJavaScript } from 'acorn';
import MagicString from 'magic-string';
import { adaptComponentProps } from './component_adapters.mjs';
import { parse as parseSvelte, VERSION } from 'svelte/compiler';

const compatibility = JSON.parse(readFileSync(new URL('./compatibility.json', import.meta.url), 'utf8'));

function unusedName(source, stem) {
  let name = stem;
  while (source.includes(name)) name += '_';
  return name;
}

function visit(node, callback) {
  if (!node || typeof node !== 'object') return;
  callback(node);
  for (const [key, value] of Object.entries(node)) {
    if (key === 'loc' || key === 'name_loc') continue;
    if (Array.isArray(value)) value.forEach(child => visit(child, callback));
    else if (value && typeof value === 'object') visit(value, callback);
  }
}

function replaceTag(source, changes, node, expression) {
  // Keep the original call site, including direct-child slot placement and bindings, in both Svelte modes.
  changes.prependLeft(node.start, '<!-- svelte-ignore svelte_component_deprecated -->');
  changes.overwrite(node.start + 1, node.start + 1 + node.name.length,
    `svelte:component this={${expression}}`);
  const closingStart = source.lastIndexOf('</', node.end - 1);
  const closing = source.slice(closingStart, node.end).match(/^<\/([\w.$:]+)\s*>$/);
  if (closingStart > node.start && closing?.[1] === node.name) {
    changes.overwrite(closingStart + 2, closingStart + 2 + node.name.length, 'svelte:component');
  }
}

export function instrumentComponents(source, id, registry) {
  const ast = parseSvelte(source, { modern: true });
  const changes = new MagicString(source);
  adaptComponentProps(source, id, changes);
  const resolve = unusedName(source, '__aihubResolve');
  const active = unusedName(source, '__aihubReplacements');
  const original = unusedName(source, '__aihubOriginal');
  let count = 0;
  let recursive = false;
  visit(ast.fragment, node => {
    if (node.type === 'SvelteComponent') {
      changes.prependLeft(node.expression.start, `${resolve}(`);
      changes.appendRight(node.expression.end, `,$${active})`);
      count++;
    } else if (node.type === 'Component' || node.type === 'SvelteSelf') {
      const self = node.type === 'SvelteSelf';
      const value = self ? `${original}(${JSON.stringify(id)})` : node.name;
      replaceTag(source, changes, node, `${resolve}(${value},$${active})`);
      recursive ||= self;
      count++;
    }
  });
  if (!count) return null;
  const imports = `\nimport {resolveComponent as ${resolve},replacements as ${active}` +
    `${recursive ? `,getOriginalComponent as ${original}` : ''}} from ${JSON.stringify(registry)};\n`;
  if (ast.instance) changes.appendLeft(ast.instance.content.start, imports);
  else changes.prepend(`<script>${imports}</script>\n`);
  return { code: changes.toString(), map: changes.generateMap({ hires: true }) };
}

export function identifyComponent(source, id, registry) {
  const ast = parseJavaScript(source, { ecmaVersion: 'latest', sourceType: 'module' });
  const declaration = ast.body.find(node => node.type === 'ExportDefaultDeclaration')?.declaration;
  const name = declaration?.type === 'Identifier' ? declaration.name : declaration?.id?.name;
  if (!name) throw new Error(`Cannot identify compiled Open WebUI component: ${id}`);
  const register = unusedName(source, '__aihubRegister');
  const changes = new MagicString(source);
  changes.append(`\nimport {registerComponent as ${register}} from ${JSON.stringify(registry)};\n` +
    `${register}(${JSON.stringify(id)},${name});\n`);
  return { code: changes.toString(), map: changes.generateMap({ hires: true }) };
}

export function componentReplacementPlugins({ registry, exclude = [] }) {
  if (VERSION !== compatibility.svelte) {
    throw new Error(`Open WebUI mod adapter requires Svelte ${compatibility.svelte}; found ${VERSION}`);
  }
  let root;
  const catalog = new Set();
  const relative = id => path.relative(root, id).split(path.sep).join('/');
  const accepts = (id, options) => !options?.ssr && id.endsWith('.svelte') &&
    (relative(id).startsWith('src/') || relative(id).startsWith('.svelte-kit/generated/')) &&
    !exclude.some(prefix => relative(id).startsWith(prefix));
  return [{
    name: 'aihub-component-usages',
    enforce: 'pre',
    configResolved(config) {
      root = realpathSync(config.root);
      const upstream = JSON.parse(readFileSync(path.join(root, 'package.json'), 'utf8'));
      if (upstream.name === 'open-webui' && upstream.version !== compatibility.openwebui) {
        throw new Error(`Open WebUI mod adapter requires ${compatibility.openwebui}; found ${upstream.version}`);
      }
    },
    transform(source, id, options) {
      if (accepts(id, options)) return instrumentComponents(source, relative(id), registry);
    }
  }, {
    name: 'aihub-component-identities',
    enforce: 'post',
    buildStart() { catalog.clear(); },
    transform(source, id, options) {
      if (!accepts(id, options) || !relative(id).startsWith('src/')) return;
      const key = relative(id);
      const result = identifyComponent(source, key, registry);
      catalog.add(key);
      return result;
    },
    generateBundle() {
      if (catalog.size) this.emitFile({
        type: 'asset', fileName: '_aihub/mods/components.json', source: JSON.stringify([...catalog].sort())
      });
    }
  }];
}
