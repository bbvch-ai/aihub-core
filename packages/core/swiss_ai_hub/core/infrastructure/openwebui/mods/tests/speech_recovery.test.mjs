import assert from 'node:assert/strict';
import test from 'node:test';
import { speechRecovery } from '../bundled/speech-recovery/request.js';

const request = (path = '/api/v1/audio/speech', init = {}) => new Request(new URL(path, 'https://webui.test'), { method: 'POST', ...init });

for (const [failure, unavailable] of [
  ['HTTP failure', () => new Response('Unavailable', { status: 503 })],
  ['network failure', () => { throw new TypeError('Failed to fetch'); }]
]) {
  test(`${failure} advances voice playback with a valid short WAV`, async () => {
    const failed = [];
    const recover = speechRecovery({ origin: 'https://webui.test', scope: () => 4, failed: turn => failed.push(turn) });
    const response = await recover(request(), unavailable);
    assert.equal(response.headers.get('Content-Type'), 'audio/wav');
    const audio = new Uint8Array(await response.arrayBuffer());
    assert.equal(new TextDecoder().decode(audio.slice(0, 4)), 'RIFF');
    assert.equal(new TextDecoder().decode(audio.slice(8, 12)), 'WAVE');
    assert.deepEqual(failed, [4]);
  });
}

test('ordinary playback, other requests and successful speech preserve the response', async () => {
  let active = null;
  const recover = speechRecovery({ origin: 'https://webui.test', scope: () => active, failed: () => assert.fail('Unexpected fallback') });
  const failure = new Response('Unavailable', { status: 503 });
  assert.equal(await recover(request(), () => failure), failure);
  active = 1;
  for (const url of ['/api/v1/audio/transcriptions', 'https://elsewhere.test/api/v1/audio/speech']) {
    assert.equal(await recover(request(url), () => failure), failure);
  }
  const success = new Response('Audio');
  assert.equal(await recover(request(), () => success), success);
});

test('cancellation and explicit handler errors are not converted into successful audio', async () => {
  const recover = speechRecovery({ origin: 'https://webui.test', scope: () => 0, failed: () => assert.fail('Unexpected fallback') });
  const controller = new AbortController();
  await assert.rejects(recover(request(undefined, { signal: controller.signal }), () => {
    controller.abort();
    throw controller.signal.reason;
  }), { name: 'AbortError' });
  const bug = new Error('Another handler failed');
  await assert.rejects(recover(request(), () => { throw bug; }), error => error === bug);
});


test('unrelated requests do not read voice state', async () => {
  const recover = speechRecovery({ origin: 'https://webui.test',
    scope: () => assert.fail('Unrelated request accessed voice state'), failed: () => assert.fail('Unexpected fallback') });
  const response = new Response('Native response');
  for (const input of [request('/api/models'), request('https://elsewhere.test/api/v1/audio/speech'), request(undefined, { method: 'GET' })]) {
    assert.equal(await recover(input, () => response), response);
  }
});
