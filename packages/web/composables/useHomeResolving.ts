// useState, not createSharedComposable: the writer is a route middleware, not a component.
export const useHomeResolving = () => useState<boolean>('home-resolving', () => false)
