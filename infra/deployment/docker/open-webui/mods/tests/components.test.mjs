import assert from 'node:assert/strict';
import { beforeEach, test } from 'node:test';
import { get } from 'svelte/store';
import { compile } from 'svelte/compiler';
import { getOriginalComponent, registerComponent, replacements, replaceComponents, resolveComponent } from '../components.mjs';
import { identifyComponent, instrumentComponents } from '../component_plugin.mjs';

beforeEach(() => replaceComponents([]));

test('matching uses component identity and preserves unrelated components', () => {
  const original = function Menu() {};
  const other = function Menu() {};
  const replacement = () => {};
  registerComponent('src/Menu.svelte', original);
  replaceComponents([['src/Menu.svelte', replacement]]);
  assert.equal(resolveComponent(original, get(replacements)), replacement);
  assert.equal(resolveComponent(other, get(replacements)), other);
  assert.equal(resolveComponent(null, get(replacements)), null);
  assert.equal(getOriginalComponent('src/Menu.svelte'), original);
  replaceComponents([]);
  assert.equal(resolveComponent(original, get(replacements)), original);
});

test('a replacement can be selected before its original component is lazily loaded', () => {
  const original = () => {};
  const replacement = () => {};
  replaceComponents([['src/Lazy.svelte', replacement]]);
  assert.throws(() => getOriginalComponent('src/Lazy.svelte'), /has not loaded/);
  registerComponent('src/Lazy.svelte', original);
  assert.equal(resolveComponent(original, get(replacements)), replacement);
});

test('conflicting or invalid replacements do not partially change active selection', () => {
  const original = () => {};
  replaceComponents([['src/Existing.svelte', original]]);
  const previous = get(replacements);
  assert.throws(() => replaceComponents([['src/New.svelte', original], ['src/New.svelte', () => {}]]), /Multiple mods/);
  assert.equal(get(replacements), previous);
  assert.throws(() => replaceComponents([['src/New.svelte', null]]), /Invalid replacement/);
  assert.equal(get(replacements), previous);
});

test('instrumented markup retains named slots, module exports and colliding user identifiers', () => {
  const source = `<script context="module">export const contract = 'kept';</script>
    <script>import Child from './Child.svelte';let value=1;let instance;const __aihubResolve=2;</script>
    <Child bind:value bind:this={instance} on:change={()=>value++}>
      <span>{value}</span><svelte:fragment slot="detail" let:result>{result}</svelte:fragment>
    </Child>`;
  const transformed = instrumentComponents(source, 'src/Parent.svelte', './registry.mjs');
  const output = compile(transformed.code, { filename: 'Parent.svelte', generate: 'client' });
  assert.ok(output.js.code.includes('contract'));
  assert.deepEqual(output.warnings, []);
  assert.ok(identifyComponent(output.js.code, 'src/Parent.svelte', './registry.mjs').code.includes('src/Parent.svelte'));
});

test('runes components retain callbacks and snippets without new deprecation warnings', () => {
  const source = `<script>import Child from './Child.svelte';let value=$state(1);</script>
    <Child bind:value onChange={()=>value++}>{#snippet detail(result)}<span>{result}</span>{/snippet}</Child>`;
  const transformed = instrumentComponents(source, 'src/Runes.svelte', './registry.mjs');
  assert.deepEqual(compile(transformed.code, { filename: 'Runes.svelte', generate: 'client' }).warnings, []);
});

test('an unexpected upstream compiled component shape fails the build', () => {
  assert.throws(() => identifyComponent('export default () => {}', 'src/Changed.svelte', './registry.mjs'), /Cannot identify/);
});
