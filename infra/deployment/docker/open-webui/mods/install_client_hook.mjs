import { existsSync, writeFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

export async function installClientHook(directory) {
  const config = (await import(pathToFileURL(resolve(directory, 'svelte.config.js')).href)).default;
  const hook = config.kit?.files?.hooks?.client ?? 'src/hooks.client';
  if (['', '.js', '.ts'].some(extension => existsSync(resolve(directory, hook + extension)))) {
    throw new Error('Open WebUI now has a client hook; compose it with the mod init hook before upgrading');
  }
  if (hook !== 'src/hooks.client') throw new Error('Open WebUI changed its client-hook location; review the mod adapter');
  writeFileSync(resolve(directory, 'src/hooks.client.js'), "export { init } from '../aihub-mods/host.mjs';\n", { flag: 'wx' });
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  await installClientHook(process.argv[2] ?? process.cwd());
}
