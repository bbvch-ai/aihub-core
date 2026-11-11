import 'svelte/internal/disclose-version';
import 'svelte/internal/flags/legacy';
import * as svelte from 'svelte';
import * as internal from 'svelte/internal/client';
import * as store from 'svelte/store';
import * as transition from 'svelte/transition';
import * as motion from 'svelte/motion';
import * as easing from 'svelte/easing';
import * as reactivity from 'svelte/reactivity';
import * as events from 'svelte/events';
import * as animate from 'svelte/animate';
import * as stores from '$lib/stores';
import { getOriginalComponent } from './components.mjs';
import { modFetch } from './request_bridge.mjs';

export { replaceComponents } from './components.mjs';
export { guardComponent } from './component_boundary.mjs';

export { compatibility, assertCompatible } from './compatibility.mjs';

const modules = {
  svelte,
  'svelte/internal/client': internal,
  'svelte/store': store,
  'svelte/transition': transition,
  'svelte/motion': motion,
  'svelte/easing': easing,
  'svelte/reactivity': reactivity,
  'svelte/events': events,
  'svelte/animate': animate,
  '@openwebui/stores': stores,
  '@aihub/mods': { getOriginalComponent, fetch: modFetch }
};

export function getModule(name) {
  if (!Object.hasOwn(modules, name)) throw new Error(`Unsupported Open WebUI mod import: ${name}`);
  return modules[name];
}

export function getExport(module, name) {
  const exports = getModule(module);
  if (!Object.hasOwn(exports, name)) throw new Error(`Unknown Open WebUI mod import: ${module}.${name}`);
  return exports[name];
}
