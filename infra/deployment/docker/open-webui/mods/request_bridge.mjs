let handler;

export function setRequestHandler(next) { handler = next; }

export function modFetch(input, init) {
  return handler ? handler(input, init) : globalThis.fetch(input, init);
}
