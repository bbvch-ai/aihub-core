import contract from './compatibility.json' with { type: 'json' };

export const compatibility = Object.freeze(contract);

export function assertCompatible(expected) {
  for (const key of ['host_protocol', 'source_commit', 'svelte', 'python']) {
    if (expected[key] !== compatibility[key]) throw new Error(`Open WebUI mod compatibility mismatch: ${key}`);
  }
}
