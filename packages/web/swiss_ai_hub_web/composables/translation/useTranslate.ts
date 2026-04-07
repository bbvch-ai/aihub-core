import { translateText, type TranslationRequest } from '@core/sdk/client'

export function useTranslate() {
  const {
    mutateAsync: translate,
    isLoading: isTranslating,
  } = useMutation({
    mutation: ({ request, tenantId }: { request: TranslationRequest, tenantId: string }) =>
      translateText({
        composable: '$fetch',
        path: { tenant_id: tenantId },
        body: request,
      }),
  })

  return {
    translate,
    isTranslating,
  }
}
