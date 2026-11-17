import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { componentReplacementPlugins } from './component_plugin.mjs';
import { modRequestPlugin } from './request_plugin.mjs';

export function openWebuiModHost() {
  const filename = name => fileURLToPath(new URL(name, import.meta.url));
  let ssr = false;
  return [
    ...componentReplacementPlugins({ registry: filename('./components.mjs') }),
    modRequestPlugin(),
    {
      name: 'aihub-mod-host',
      configResolved(config) { ssr = Boolean(config.build.ssr); },
      buildStart() {
        if (ssr) return;
        for (const entry of ['runtime', 'host']) {
          this.emitFile({
            type: 'chunk', id: filename(`./${entry}.mjs`),
            fileName: `_aihub/mods/${entry}.js`, preserveSignature: 'strict'
          });
        }
        this.emitFile({
          type: 'asset', fileName: '_aihub/mods/compatibility.json',
          source: readFileSync(filename('./compatibility.json'), 'utf8')
        });
      }
    }
  ];
}
