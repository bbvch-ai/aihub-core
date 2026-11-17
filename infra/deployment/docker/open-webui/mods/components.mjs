import { writable } from 'svelte/store';

const identities = new WeakMap();
const originals = new Map();
export const replacements = writable(new Map());

export function registerComponent(id, component) {
  identities.set(component, id);
  originals.set(id, component);
}

export function resolveComponent(component, active) {
  return active.get(identities.get(component)) ?? component;
}

export function getOriginalComponent(id) {
  const component = originals.get(id);
  if (!component) throw new Error(`Open WebUI component has not loaded: ${id}`);
  return component;
}

export function replaceComponents(entries) {
  const next = new Map();
  for (const [id, component] of entries) {
    if (next.has(id)) throw new Error(`Multiple mods replace the same component: ${id}`);
    if (typeof component !== 'function') throw new Error(`Invalid replacement component: ${id}`);
    next.set(id, component);
  }
  replacements.set(next);
}
