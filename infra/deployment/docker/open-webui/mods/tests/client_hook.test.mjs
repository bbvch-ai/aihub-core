import assert from 'node:assert/strict';
import { mkdtemp, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import { test } from 'node:test';
import { installClientHook } from '../install_client_hook.mjs';

async function fixture(t, config = '{}') {
  const directory = await mkdtemp(join(tmpdir(), 'aihub-client-hook-'));
  t.after(() => rm(directory, { recursive: true, force: true }));
  await mkdir(join(directory, 'src'));
  await writeFile(join(directory, 'package.json'), '{"type":"module"}');
  await writeFile(join(directory, 'svelte.config.js'), `export default ${config};`);
  return directory;
}

test('the client hook uses the supported framework entry and refuses to overwrite an existing hook', async t => {
  const directory = await fixture(t);
  await installClientHook(directory);
  const path = join(directory, 'src/hooks.client.js');
  const content = await readFile(path, 'utf8');
  assert.equal(content, "export { init } from '../aihub-mods/host.mjs';\n");
  await assert.rejects(installClientHook(directory), /now has a client hook/);
  assert.equal(await readFile(path, 'utf8'), content);
});

test('an upstream TypeScript hook requires an explicit compatibility review', async t => {
  const directory = await fixture(t);
  await writeFile(join(directory, 'src/hooks.client.ts'), 'export function init() {}');
  await assert.rejects(installClientHook(directory), /now has a client hook/);
});

test('a custom upstream hook location cannot be silently bypassed', async t => {
  const directory = await fixture(t, '{ kit: { files: { hooks: { client: "src/other-hook" } } } }');
  await assert.rejects(installClientHook(directory), /changed its client-hook location/);
});
