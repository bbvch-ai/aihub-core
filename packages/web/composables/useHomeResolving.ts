// Shared flag that drives app.vue's spinner overlay while the home-redirect
// middleware resolves tenants. Uses useState (not createSharedComposable) since
// the writer is a route middleware, not a component.
export const useHomeResolving = () => useState<boolean>('home-resolving', () => false)
