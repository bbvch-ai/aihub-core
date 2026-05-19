// Runtime configuration for the sysadmin-web static SPA. See the sibling
// comment in @swiss-ai-hub/web's config.template.js for the mechanism — the
// nginx entrypoint envsubst's this into /config.js, loaded synchronously in
// <head> before the app. The inherited plugins/0.runtime-config.client.ts
// (from the web layer) reads window.__AIHUB_CONFIG__.
window.__AIHUB_CONFIG__ = {
  OAUTH_CLIENT_ID: '${OAUTH_CLIENT_ID}',
  OAUTH_AUTHORITY_URL: '${OAUTH_AUTHORITY_URL}',
  MAIN_API_URL: '${MAIN_API_URL}',
  MAIN_APP_URL: '${MAIN_APP_URL}',
  API_BASE_URL: '${MAIN_API_URL}/api/v1',
}
