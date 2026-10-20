// Keycloak's SSO cookie is a session cookie, so it can only vanish when the
// browser session ends — and sessionStorage ends with it. Once the cookie has
// been seen in this tab, later page loads can skip the costly prompt=none probe
// in middleware/auth.global.ts. Storing the subject makes a different user in
// the same tab probe again.
const SSO_SESSION_CHECKED_KEY = 'aihub_sso_session_checked'

export const isSsoSessionChecked = (sub: string): boolean =>
  sessionStorage.getItem(SSO_SESSION_CHECKED_KEY) === sub

export const markSsoSessionChecked = (sub: string): void => {
  sessionStorage.setItem(SSO_SESSION_CHECKED_KEY, sub)
}
