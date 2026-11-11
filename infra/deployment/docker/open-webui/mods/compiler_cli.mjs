import { readFile, writeFile } from 'node:fs/promises';
import { prepareModPublication } from './compiler.mjs';

const [sourcePath, catalogPath, outputPath] = process.argv.slice(2);
if (!sourcePath || !catalogPath || !outputPath || process.argv.length !== 5) {
  throw new Error('Usage: compiler-cli.mjs source.zip host.json publication.zip');
}
const source = await readFile(sourcePath);
if (source.length > 16 * 1024 * 1024) throw new Error('Source archive exceeds 16 MiB');
const catalog = JSON.parse(await readFile(catalogPath, 'utf8'));
const result = await prepareModPublication(new Uint8Array(source), catalog.components, catalog.callables);
await writeFile(outputPath, result.archive);
process.stdout.write(JSON.stringify({ source_revision: result.source_revision, warnings: result.warnings }) + '\n');
