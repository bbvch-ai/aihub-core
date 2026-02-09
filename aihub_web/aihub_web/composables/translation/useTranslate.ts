import { translateText, type TranslationRequest } from '@core/sdk/client'

export function useTranslate() {
  const {
    mutateAsync: translate,
    isLoading: isTranslating,
  } = useMutation({
    mutation: (request: TranslationRequest) =>
      translateText({
        composable: '$fetch',
        body: request,
      }),
  })

  return {
    translate,
    isTranslating,
  }
}
