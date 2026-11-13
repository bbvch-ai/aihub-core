import { compile, compileModule, preprocess, VERSION } from 'svelte/compiler';
import { parse } from 'acorn';
import MagicString from 'magic-string';
import compatibility from './compatibility.json' with { type: 'json' };
import { scriptEntries } from './script_entries.mjs';

const sharedModules = new Set([
  'svelte', 'svelte/internal/client', 'svelte/store', 'svelte/transition', 'svelte/motion',
  'svelte/easing', 'svelte/reactivity', 'svelte/events', 'svelte/animate', '@openwebui/stores',
  '@openwebui/shortcuts', '@aihub/mods'
]);
const hostSideEffects = new Set(['svelte/internal/disclose-version', 'svelte/internal/flags/legacy']);

function useHostRuntime(source, nativeRuntime) {
  const changes = new MagicString(source);
  const ast = parse(source, { ecmaVersion: 'latest', sourceType: 'module' });
  const dependencies = new Set();
  let runtime = '__aihubModRuntime';
  while (source.includes(runtime)) runtime += '_';
  function relativeImport(node) {
    const name = node.value;
    if (typeof name !== 'string' || !(name.startsWith('./') || name.startsWith('../'))) return false;
    dependencies.add(name);
    changes.overwrite(node.start, node.end, JSON.stringify(`${name}.mjs`));
    return true;
  }
  for (const node of ast.body) {
    if (!['ImportDeclaration', 'ExportNamedDeclaration', 'ExportAllDeclaration'].includes(node.type) || !node.source) continue;
    if (node.attributes?.length) throw new Error('Import attributes are not supported; import JSON directly');
    const name = node.source.value === '$lib/stores' ? '@openwebui/stores' : node.source.value;
    if (relativeImport(node.source)) {
      if (!isModule(name) && node.type === 'ImportDeclaration' && !node.specifiers.length) {
        throw new Error(`Import the asset URL or JSON value explicitly: ${name}`);
      }
      if (!isModule(name) && node.specifiers?.some(binding => binding.type === 'ImportSpecifier' && binding.imported.name !== 'default')) {
        throw new Error(`Asset modules expose a default export: ${name}`);
      }
      continue;
    }
    if (!nativeRuntime) throw new Error(`Bootstrap imports must stay within the package: ${name}`);
    if (node.type !== 'ImportDeclaration') throw new Error(`Re-export shared modules through a local import: ${name}`);
    if (hostSideEffects.has(name) && !node.specifiers.length) {
      changes.remove(node.start, node.end);
      continue;
    }
    if (!sharedModules.has(name)) throw new Error(`Unsupported Open WebUI mod import: ${name}`);
    const imported = `${runtime}.getModule(${JSON.stringify(name)})`;
    const bindings = node.specifiers.map(specifier => {
      if (specifier.type === 'ImportNamespaceSpecifier') return `const ${specifier.local.name}=${imported};`;
      const exported = specifier.type === 'ImportDefaultSpecifier' ? 'default' : specifier.imported.name ?? specifier.imported.value;
      return `const ${specifier.local.name}=${runtime}.getExport(${JSON.stringify(name)},${JSON.stringify(exported)});`;
    });
    changes.overwrite(node.start, node.end, bindings.join('\n'));
  }
  visitNodes(ast, node => {
    if (node.type === 'ImportExpression' && node.options) throw new Error('Dynamic import options are not supported');
    if (node.type === 'ImportExpression' && !relativeImport(node.source)) {
      throw new Error('Dynamic imports must name a relative package file explicitly');
    }
    if (node.type !== 'NewExpression' || node.callee.name !== 'URL' || node.arguments.length !== 2) return;
    const [path, base] = node.arguments;
    if (base.type !== 'MemberExpression' || base.computed || base.property.name !== 'url' ||
        base.object.type !== 'MetaProperty' || base.object.meta.name !== 'import') return;
    if (typeof path.value !== 'string') throw new Error('Package asset URLs must name a file explicitly');
    if (!path.value.startsWith('./') && !path.value.startsWith('../')) return;
    dependencies.add(path.value);
    if (isModule(path.value)) changes.overwrite(path.start, path.end, JSON.stringify(`${path.value}.mjs`));
  });
  if (nativeRuntime) {
    changes.prepend(`const ${runtime}=await import(new URL('/_aihub/mods/runtime.js',location.origin).href);\n` +
      `${runtime}.assertCompatible(${JSON.stringify(compatibility)});\n`);
  }
  return { code: changes.toString(), dependencies: [...dependencies] };
}

function visitNodes(node, visit) {
  if (!node || typeof node !== 'object') return;
  if (node.type) visit(node);
  for (const value of Object.values(node)) {
    if (Array.isArray(value)) value.forEach(child => visitNodes(child, visit));
    else if (value && typeof value === 'object') visitNodes(value, visit);
  }
}

function isModule(filename) {
  return /\.(svelte|m?js|ts)$/.test(filename);
}

async function stripTypes(source, filename) {
  const { default: ts } = await import('typescript');
  const result = ts.transpileModule(source, {
    fileName: filename,
    reportDiagnostics: true,
    compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022, verbatimModuleSyntax: true }
  });
  const errors = result.diagnostics?.filter(diagnostic => diagnostic.category === ts.DiagnosticCategory.Error) ?? [];
  if (errors.length) throw new Error(ts.flattenDiagnosticMessageText(errors[0].messageText, '\n'));
  return result.outputText;
}

export async function compileModFile(source, filename, { nativeRuntime = true } = {}) {
  if (VERSION !== compatibility.svelte) throw new Error('Open WebUI mod compiler version does not match the host');
  if (typeof source !== 'string') throw new Error(`Expected text source: ${filename}`);
  if (!nativeRuntime && /\.svelte(?:\.[jt]s)?$/.test(filename)) {
    throw new Error(`Bootstrap cannot initialize Svelte code: ${filename}`);
  }
  let code = source;
  let warnings = [];
  if (filename.endsWith('.svelte')) {
    const processed = await preprocess(source, {
      script: async ({ content, attributes }) => attributes.lang === 'ts'
        ? { code: await stripTypes(content, `${filename}.ts`) }
        : undefined
    }, { filename });
    const result = compile(processed.code, { filename, generate: 'client', dev: false, css: 'injected' });
    for (const match of (result.ast.css?.content.styles ?? '').matchAll(/url\(\s*([^)]*)\)/gi)) {
      const url = match[1].trim().replace(/^(['"])(.*)\1$/, '$2');
      if (!/^(?:[a-z][\w+.-]*:|\/|#)/i.test(url)) {
        throw new Error('Relative CSS URLs need an imported asset URL in a style attribute');
      }
    }
    code = result.js.code;
    warnings = result.warnings;
  } else {
    if (!filename.endsWith('.js') && !filename.endsWith('.mjs') && !filename.endsWith('.ts')) {
      throw new Error(`Unsupported mod source file: ${filename}`);
    }
    if (filename.endsWith('.ts')) code = await stripTypes(code, filename);
    if (/\.svelte\.[jt]s$/.test(filename)) {
      const result = compileModule(code, { filename, generate: 'client', dev: false });
      code = result.js.code;
      warnings = result.warnings;
    }
  }
  return {
    filename: `${filename}.mjs`,
    ...useHostRuntime(code, nativeRuntime),
    compatibility,
    warnings: warnings.map(({ code, message, start, end }) => ({ code, message, start, end }))
  };
}

function resolveDependency(filename, requested) {
  if (/[\\:%?#\u0000-\u001f\u007f]/.test(requested)) throw new Error(`Unsupported package import: ${requested}`);
  const segments = filename.split('/').slice(0, -1);
  for (const segment of requested.split('/')) {
    if (segment === '.') continue;
    if (segment === '..') {
      if (!segments.length) throw new Error(`Import leaves the mod package: ${requested}`);
      segments.pop();
    } else {
      if (!segment) throw new Error(`Empty path segment in package import: ${requested}`);
      segments.push(segment);
    }
  }
  return segments.join('/');
}

function decodeSource(content, filename) {
  if (typeof content === 'string') return content;
  try { return new TextDecoder('utf-8', { fatal: true }).decode(content); }
  catch { throw new Error(`Source must be UTF-8: ${filename}`); }
}

function compileAsset(content, filename) {
  if (filename.endsWith('.py') || filename === 'mod.json') throw new Error(`Not a frontend asset: ${filename}`);
  const code = filename.endsWith('.json')
    ? `export default JSON.parse(${JSON.stringify(JSON.stringify(JSON.parse(decodeSource(content, filename))))});`
    : `export default new URL(${JSON.stringify('./' + filename.split('/').at(-1))},import.meta.url).href;`;
  return { filename: `${filename}.mjs`, code, dependencies: [], warnings: [] };
}

export async function compileModPackage(manifest, sourceFiles, componentIds) {
  const sources = new Map(Object.entries(sourceFiles));
  const targets = new Set(componentIds);
  for (const target of Object.keys(manifest.replacements ?? {})) {
    if (!targets.has(target)) throw new Error(`Replacement target is absent from this Open WebUI host: ${target}`);
  }
  const pending = Object.entries(scriptEntries).filter(([name]) => manifest[name])
    .map(([name, definition]) => ({ filename: manifest[name], definition }));
  pending.push(...Object.values(manifest.replacements ?? {}).map(filename => ({ filename, definition: scriptEntries.frontend })));
  const visited = new Set();
  const files = new Map();
  const warnings = [];
  function emit(filename, content) {
    if (files.has(filename)) throw new Error(`Conflicting compiled output path: ${filename}`);
    files.set(filename, content);
  }
  while (pending.length) {
    const { filename, definition } = pending.shift();
    const { prefix, nativeRuntime } = definition;
    const key = `${prefix}:${filename}`;
    if (visited.has(key)) continue;
    visited.add(key);
    if (!sources.has(filename)) throw new Error(`Missing package dependency: ${filename}`);
    const content = sources.get(filename);
    try {
      const compiled = isModule(filename)
        ? await compileModFile(decodeSource(content, filename), filename, { nativeRuntime })
        : compileAsset(content, filename);
      emit(prefix + compiled.filename, compiled.code);
      if (!isModule(filename)) emit(prefix + filename, content);
      for (const dependency of compiled.dependencies) {
        const resolved = resolveDependency(filename, dependency);
        if (!sources.has(resolved)) throw new Error(`Missing package dependency: ${resolved}`);
        pending.push({ filename: resolved, definition });
      }
      warnings.push(...compiled.warnings.map(warning => ({ ...warning, filename })));
    } catch (error) {
      error.message = `${filename}: ${error.message}`;
      error.filename = filename;
      throw error;
    }
  }
  return {
    compatibility,
    ...Object.fromEntries(Object.entries(scriptEntries).map(([name, definition]) =>
      [name, manifest[name] ? `${definition.prefix}${manifest[name]}.mjs` : null])),
    replacements: Object.fromEntries(Object.entries(manifest.replacements ?? {}).map(([target, source]) =>
      [target, `${scriptEntries.frontend.prefix}${source}.mjs`])),
    files: Object.fromEntries(files),
    warnings
  };
}

export async function prepareModPublication(sourceArchive, componentIds, callables = {}) {
  // Fetch this archive from the validating SysAdmin API; JSZip is not the upload validator.
  const { default: JSZip } = await import('jszip');
  const source = await JSZip.loadAsync(sourceArchive);
  const files = Object.fromEntries(await Promise.all(Object.values(source.files)
    .filter(file => !file.dir).map(async file => [file.name, await file.async('uint8array')])));
  const manifest = JSON.parse(decodeSource(files['mod.json'], 'mod.json'));
  const backendTargets = {};
  for (const target of Object.keys(manifest.backend_overrides ?? {})) {
    if (!Object.hasOwn(callables, target)) throw new Error(`Backend callable target is absent from this Open WebUI host: ${target}`);
    backendTargets[target] = callables[target];
  }
  const compiled = await compileModPackage(manifest, files, componentIds);
  const digest = await crypto.subtle.digest('SHA-256', sourceArchive);
  const sourceRevision = [...new Uint8Array(digest)].map(value => value.toString(16).padStart(2, '0')).join('');
  const publication = new JSZip();
  const options = { date: new Date('1980-01-01T00:00:00Z'), createFolders: false };
  publication.file('publication.json', JSON.stringify({
    format: 1, source_revision: sourceRevision, compatibility,
    bootstrap: compiled.bootstrap, frontend: compiled.frontend,
    replacements: compiled.replacements, backend_targets: backendTargets,
    warnings: compiled.warnings.map(warning => warning.filename ? `${warning.filename}: ${warning.message}` : warning.message)
  }), options);
  for (const filename of Object.keys(compiled.files).sort()) {
    publication.file(`files/${filename}`, compiled.files[filename], options);
  }
  return {
    source_revision: sourceRevision,
    archive: await publication.generateAsync({ type: 'uint8array', compression: 'DEFLATE' }),
    warnings: compiled.warnings
  };
}
