// Native voice playback needs a cached audio item to advance its sentence queue.
const silentClip = 'UklGRnQAAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YVAAAACAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgICAgA==';

export function speechRecovery({ origin, scope, failed }) {
  return async (request, next) => {
    const url = new URL(request.url);
    if (url.origin !== origin || url.pathname !== '/api/v1/audio/speech' || request.method !== 'POST') {
      return next();
    }
    const turn = scope();
    if (turn === null) return next();
    try {
      const response = await next();
      if (response.ok) return response;
    } catch (error) {
      if (request.signal.aborted || !(error instanceof TypeError)) throw error;
    }
    request.signal.throwIfAborted();
    failed(turn);
    return new Response(Uint8Array.from(atob(silentClip), char => char.charCodeAt(0)), {
      headers: { 'Content-Type': 'audio/wav' }
    });
  };
}
