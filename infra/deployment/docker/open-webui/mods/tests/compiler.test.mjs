import assert from 'node:assert/strict';
import { test } from 'node:test';
import { compileModFile, compileModPackage, prepareModPublication } from '../compiler.mjs';

const target = 'src/lib/Menu.svelte';
const manifest = { replacements: { [target]: 'frontend/Menu.svelte' } };
const compile = (files, overrides = {}, targets = [target]) => compileModPackage({ ...manifest, ...overrides }, files, targets);

test('backend publication captures native source fingerprints without executing source', async () => {
  const { default: JSZip } = await import('jszip');
  const callable = 'open_webui.routers.users:get_user_info_by_session_user';
  const fingerprint = { source_sha256: 'a'.repeat(64) };
  const source = new JSZip();
  source.file('mod.json', JSON.stringify({ format: 1, id: 'native-info', backend: 'main.py', backend_overrides: { [callable]: 'info' } }));
  source.file('main.py', 'raise RuntimeError("Compilation must not execute Python")');
  const archive = await source.generateAsync({ type: 'uint8array' });
  await assert.rejects(prepareModPublication(archive, []), /Backend callable target is absent/);
  const prepared = await prepareModPublication(archive, [], { [callable]: fingerprint });
  const publication = await JSZip.loadAsync(prepared.archive);
  const metadata = JSON.parse(await publication.file('publication.json').async('string'));
  assert.deepEqual(metadata.backend_targets, { [callable]: fingerprint });
  assert.deepEqual(Object.keys(publication.files), ['publication.json']);
});

test('Svelte TypeScript scripts and template expressions compile to the shared runtime', async () => {
  const result = await compile({
    'frontend/Menu.svelte': `<script lang="ts">
      import type { Snippet } from 'svelte';
      import Child from './Child.svelte';
      interface Props { initial?: number; children?: Snippet }
      let { initial = 2 }: Props = $props();
      let count = $state<number>(initial);
    </script><button onclick={() => count++}>{count as number}</button><Child value={count}/>` ,
    'frontend/Child.svelte': '<script lang="ts">let { value }: { value: number } = $props();</script><span>{value}</span>'
  });
  const code = result.files['frontend/Menu.svelte.mjs'];
  assert.match(code, /getModule\("svelte\/internal\/client"\)/);
  assert.match(code, /Child\.svelte\.mjs/);
  assert.doesNotMatch(code, /interface Props|import type|\$state<number>|as number/);
});

test('TypeScript enums and constructor properties work inside Svelte scripts', async () => {
  const result = await compile({
    'frontend/Menu.svelte': `<script lang="ts">
      enum Mode { Compact = 'compact', Full = 'full' }
      class Label { constructor(public value: string) {} }
      const label = new Label(Mode.Compact);
    </script><span>{label.value}</span>`
  });
  assert.match(result.files['frontend/Menu.svelte.mjs'], /compact/);
  assert.doesNotMatch(result.files['frontend/Menu.svelte.mjs'], /enum Mode|public value/);
});

test('compilation accepts type mismatches but rejects invalid TypeScript syntax', async () => {
  await compile({ 'frontend/Menu.svelte': '<script lang="ts">let value: number = "text";</script><span>{value}</span>' });
  await assert.rejects(compile({ 'frontend/Menu.svelte': '<script lang="ts">let value: = 1;</script>' }));
});

test('a package follows Svelte, TypeScript, runes, re-exports and literal dynamic imports', async () => {
  const result = await compile({
    'frontend/Menu.svelte': `<script>import Child from './Child.svelte';import { count } from './state.svelte.ts';</script><Child value={count.value}/><style>:global(body){color:inherit}</style>`,
    'frontend/Child.svelte': '<script>export let value;</script><button>{value}</button>',
    'frontend/state.svelte.ts': 'import { increment } from "./reexport.js";export const count = $state({ value: increment(1) });',
    'frontend/reexport.js': 'export { increment } from "./math.ts";export const lazy = () => import("./Lazy.svelte");',
    'frontend/math.ts': 'export const increment = (value: number): number => value + 1;',
    'frontend/Lazy.svelte': '<span>Lazy</span>',
    'backend/mod.py': 'raise RuntimeError("Never run by the compiler")',
    'backend/private.json': '{"private":true}'
  });
  assert.equal(Object.keys(result.files).length, 6);
  assert.match(result.files['frontend/state.svelte.ts.mjs'], /getModule\("svelte\/internal\/client"\)/);
  assert.match(result.files['frontend/reexport.js.mjs'], /import\("\.\/Lazy.svelte.mjs"\)/);
  assert.equal(result.replacements[target], 'frontend/Menu.svelte.mjs');
  assert.equal(result.frontend, null);
  assert.deepEqual(result.warnings, []);
  assert.ok(!Object.keys(result.files).some(path => path.startsWith('backend/')));
});

test('frontend entries can use cycles and shared dependencies without duplicate output', async () => {
  const result = await compile({
    'main.js': 'export { value } from "./shared.js";import "./cycle.js";',
    'shared.js': 'export const value = 1;',
    'cycle.js': 'import "./main.js";import "./shared.js";'
  }, { frontend: 'main.js', replacements: {} });
  assert.deepEqual(Object.keys(result.files).sort(), ['cycle.js.mjs', 'main.js.mjs', 'shared.js.mjs']);
  assert.equal(result.frontend, 'main.js.mjs');
});

test('assets are explicit and resolve relative to published modules', async () => {
  const icon = new Uint8Array([137, 80, 78, 71]);
  const result = await compile({
    'frontend/Menu.svelte': `<script>import icon from '../assets/icon.png';import labels from '../assets/labels.json';</script><img src={icon} alt={labels.title}/>` ,
    'assets/icon.png': icon,
    'assets/labels.json': '{"title":"Tools","__proto__":{"safe":true}}',
    'assets/unused.png': new Uint8Array([0])
  });
  assert.deepEqual(result.files['assets/icon.png'], icon);
  assert.match(result.files['assets/icon.png.mjs'], /new URL\("\.\/icon.png",import.meta.url\)/);
  const labels = await import('data:text/javascript,' + encodeURIComponent(result.files['assets/labels.json.mjs']));
  assert.equal(labels.default.title, 'Tools');
  assert.equal(Object.getPrototypeOf(labels.default), Object.prototype);
  assert.ok(Object.hasOwn(labels.default, '__proto__'));
  assert.ok(!Object.hasOwn(result.files, 'assets/unused.png'));
});

test('new URL includes assets and rewrites module URLs', async () => {
  const result = await compile({
    'main.js': 'export const asset=new URL("./icon.svg",import.meta.url);export const worker=new URL("./worker.ts",import.meta.url);',
    'icon.svg': '<svg/>',
    'worker.ts': 'export const value: number = 1;'
  }, { frontend: 'main.js', replacements: {} });
  assert.match(result.files['main.js.mjs'], /new URL\("\.\/icon.svg",import.meta.url\)/);
  assert.match(result.files['main.js.mjs'], /new URL\("\.\/worker.ts.mjs",import.meta.url\)/);
  assert.ok(Object.hasOwn(result.files, 'icon.svg'));
  assert.ok(Object.hasOwn(result.files, 'worker.ts.mjs'));
});

for (const [source, error] of [
  ['import "./missing.js";', /Missing package dependency: missing.js/],
  ['import "../outside.js";', /leaves the mod package/],
  ['import "some-library";', /Unsupported Open WebUI mod import/],
  ['const path="./file.js";import(path);', /Dynamic imports must name/],
  ['import("https://example.com/module.js");', /Dynamic imports must name/],
  ['import value from "./labels.json" with { type: "json" };', /Import attributes are not supported/],
  ['import("./labels.json", {with: {type: "json"}});', /Dynamic import options are not supported/],
  ['import icon from "./icon.svg?raw";', /Unsupported package import/],
  ['import code from "./mod.py";', /Not a frontend asset/],
  ['import "./style.css";', /Import the asset URL/],
  ['import { title } from "./labels.json";', /default export/]
]) {
  test(`invalid dependencies fail before publication: ${source}`, async () => {
    await assert.rejects(compile({ 'main.js': source, 'mod.py': '' }, { frontend: 'main.js', replacements: {} }), error);
  });
}

test('missing targets and invalid source report the actual integration or file', async () => {
  await assert.rejects(compile({}, {}, []), /Replacement target is absent/);
  await assert.rejects(compile({ 'frontend/Menu.svelte': '<script>const =;</script>' }), error =>
    error.filename === 'frontend/Menu.svelte' && error.code === 'js_parse_error');
  await assert.rejects(compile({ 'frontend/Menu.svelte': new Uint8Array([255]) }), /must be UTF-8/);
});

test('relative CSS URLs fail explicitly instead of resolving against the chat route', async () => {
  await assert.rejects(compileModFile('<style>button{background:url("./icon.svg")}</style><button>Hi</button>', 'Menu.svelte'), /imported asset URL/);
});

test('backend-only source produces no browser files', async () => {
  const result = await compile({ 'backend/mod.py': 'raise RuntimeError()' }, { replacements: {}, backend: 'backend/mod.py' });
  assert.deepEqual(result.files, {});
});

test('publication ZIPs bind source and host and separate metadata from frontend files', async () => {
  const { default: JSZip } = await import('jszip');
  const source = new JSZip();
  source.file('mod.json', JSON.stringify({ format: 1, id: 'tools', name: 'Tools', version: '1',
    ...manifest, backend: 'backend/mod.py' }));
  source.file('frontend/Menu.svelte', '<button>Tools</button>');
  source.file('backend/mod.py', 'raise RuntimeError("Not executed")');
  const archive = await source.generateAsync({ type: 'uint8array' });
  const first = await prepareModPublication(archive, [target]);
  const second = await prepareModPublication(archive, [target]);
  assert.deepEqual(first.archive, second.archive);
  const publication = await JSZip.loadAsync(first.archive);
  assert.deepEqual(Object.keys(publication.files).sort(), ['files/frontend/Menu.svelte.mjs', 'publication.json']);
  const metadata = JSON.parse(await publication.file('publication.json').async('string'));
  assert.equal(metadata.source_revision, first.source_revision);
  assert.equal(metadata.compatibility.python, '3.11');
  assert.equal(metadata.replacements[target], 'frontend/Menu.svelte.mjs');
});
