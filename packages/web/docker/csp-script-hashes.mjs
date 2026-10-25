// Prints the CSP hash sources of every inline script in the generated HTML. Nuxt inlines its runtime config into each
// page, so `script-src 'self'` alone would block the app; the hashes allow exactly those scripts and nothing else.
import { createHash } from 'node:crypto'
import { readdirSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

const publicDir = process.argv[2]
const inlineScript = /<script(?![^>]*\ssrc=)(?![^>]*\stype="application\/json")[^>]*>([\s\S]*?)<\/script>/g

const hashes = new Set()
for (const file of readdirSync(publicDir, { recursive: true })) {
  if (!String(file).endsWith('.html')) continue
  for (const [, body] of readFileSync(join(publicDir, String(file)), 'utf8').matchAll(inlineScript)) {
    if (body) hashes.add(`'sha256-${createHash('sha256').update(body).digest('base64')}'`)
  }
}
process.stdout.write([...hashes].sort().join(' '))
