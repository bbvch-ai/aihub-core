let handler;

export function setRequestHandler(next) { handler = next; }

export function modFetch(input, init) {
  return handler ? handler(input, init) : globalThis.fetch(input, init);
}

export async function runRequestHandlers(handlers, request, send, signal) {
  const cancellation = AbortSignal.any([signal, request.signal]);
  async function dispatch(index, request) {
    cancellation.throwIfAborted();
    if (!(request instanceof Request)) {
      throw new Error('Open WebUI mod request handlers must forward a Request. Please contact your administrator.');
    }
    request = new Request(request, { signal: AbortSignal.any([cancellation, request.signal]) });
    request.signal.throwIfAborted();
    const response = await (index === handlers.length ? send(request)
      : handlers[index](request, (next = request) => dispatch(index + 1, next)));
    request.signal.throwIfAborted();
    if (!(response instanceof Response)) {
      throw new Error('Open WebUI mod request handlers must return a Response. Please contact your administrator.');
    }
    return response;
  }
  return dispatch(0, request);
}
