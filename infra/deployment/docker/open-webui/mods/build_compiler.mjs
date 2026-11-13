import { build } from 'esbuild';
import { fileURLToPath } from 'node:url';

const outfile = process.argv[2];
if (!outfile) throw new Error('Provide the output compiler filename');
await build({
  entryPoints: [fileURLToPath(new URL('./compiler_cli.mjs', import.meta.url))],
  outfile,
  bundle: true,
  platform: 'node',
  format: 'esm',
  target: 'node22',
  banner: { js: 'import { createRequire } from "node:module"; const require = createRequire(import.meta.url);' +
    'const __filename = import.meta.filename; const __dirname = import.meta.dirname;' }
});
