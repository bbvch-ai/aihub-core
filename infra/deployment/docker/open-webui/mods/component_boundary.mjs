import { boundary } from 'svelte/internal/client';

export function guardComponent(component, onError) {
  if (typeof component !== 'function') throw new Error('Replacement must export a Svelte component');
  return (anchor, props) => {
    let instance;
    // Passing the original props object preserves bindings, events, slots and exported instance methods.
    boundary(anchor, { onerror: error => queueMicrotask(() => onError(error)) }, childAnchor => {
      instance = component(childAnchor, props);
    });
    return instance;
  };
}
