import { fileURLToPath } from 'node:url';
import MagicString from 'magic-string';
import ts from 'typescript';

function fetchCalls(source, id) {
  const tree = ts.createSourceFile(id, source, ts.ScriptTarget.Latest, true, ts.ScriptKind.TS);
  const calls = [];
  const bindsFetch = name => name && (ts.isIdentifier(name) ? name.text === 'fetch'
    : (ts.isObjectBindingPattern(name) || ts.isArrayBindingPattern(name)) && name.elements.some(item => bindsFetch(item.name)));
  function visit(node) {
    if ((ts.isVariableDeclaration(node) || ts.isParameter(node) || ts.isFunctionDeclaration(node)
      || ts.isImportSpecifier(node) || ts.isImportClause(node) || ts.isNamespaceImport(node)) && bindsFetch(node.name)) {
      throw new Error(`Open WebUI API shadows fetch; review its request adapter: ${id}`);
    }
    if (ts.isCallExpression(node) && ts.isIdentifier(node.expression) && node.expression.text === 'fetch') {
      calls.push([node.expression.getStart(tree), node.expression.end]);
    }
    ts.forEachChild(node, visit);
  }
  visit(tree);
  return calls;
}

export function modRequestPlugin() {
  let ssr = false;
  let transformed = false;
  return {
    name: 'aihub-native-requests',
    enforce: 'pre',
    configResolved(config) { ssr = Boolean(config.build.ssr); },
    transform(source, id, options) {
      if (options?.ssr || !id.includes('/src/lib/apis/') || !/\.[jt]s$/.test(id)) return;
      if (id.endsWith('/src/lib/apis/openai/index.ts')) {
        if ([...source.matchAll(/fetch\(`\$\{url\}\/chat\/completions`, \{/g)].length !== 2) {
          throw new Error('Open WebUI chat request adapter changed; review its two completion callers');
        }
        transformed = true;
      }
      const positions = fetchCalls(source, id);
      if (!positions.length) return;
      if (source.includes('__aihubModFetch')) throw new Error(`Open WebUI uses the reserved request adapter name: ${id}`);
      const changes = new MagicString(source);
      for (const [start, end] of positions) changes.overwrite(start, end, '__aihubModFetch');
      changes.prepend(`import {modFetch as __aihubModFetch} from ${JSON.stringify(fileURLToPath(new URL('./request_bridge.mjs', import.meta.url)))};\n`);
      return { code: changes.toString(), map: changes.generateMap({ hires: true }) };
    },
    buildEnd(error) {
      if (!error && !ssr && !transformed) throw new Error('Open WebUI chat request adapter did not find its API module');
    }
  };
}
