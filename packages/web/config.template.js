// Runtime configuration for the static SPA. The nginx container entrypoint
// runs `envsubst` on this template at startup and writes the result to
// /config.js, which index.html loads as a classic <script> in <head> — i.e.
// synchronously, BEFORE Nuxt's deferred ES-module entry. plugins/
// 0.runtime-config.client.ts reads globalThis.__AIHUB_CONFIG__ with no fetch,
// no async, no plugin-ordering concerns. One image, many environments.
globalThis.__AIHUB_CONFIG__ = {
  OAUTH_CLIENT_ID: '${OAUTH_CLIENT_ID}',
  OAUTH_AUTHORITY_URL: '${OAUTH_AUTHORITY_URL}',
  WEBUI_URL: '${WEBUI_URL}',
  WS_ENDPOINT: '${WS_ENDPOINT}',
  SYSADMIN_URL: '${SYSADMIN_URL}',
}
