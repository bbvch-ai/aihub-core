import {type ModelDTO} from '@core/sdk/client'

export const useModelsUtils = () => {
  const {t} = useI18n()
  const toast = useToast()

  const getModeSeverity = (mode: string): string => {
    switch (mode) {
      case 'chat':
        return 'info'
      case 'embedding':
        return 'success'
      case 'image_generation':
        return 'warn'
      case 'audio_transcription':
      case 'audio_speech':
        return 'help'
      default:
        return 'secondary'
    }
  }

  const formatTokenLimits = (model: ModelDTO): string => {
    const input = model?.model_info?.max_input_tokens
    const output = model?.model_info?.max_output_tokens

    if (input && output) {
      return `${formatNumber(input)} / ${formatNumber(output)}`
    } else if (input) {
      return `${formatNumber(input)} / -`
    } else if (output) {
      return `- / ${formatNumber(output)}`
    }
    return '- / -'
  }

  const formatCostPer1M = (costPerToken?: number): string => {
    if (!costPerToken) return '-'
    const costPer1M = costPerToken * 1000000
    return `$${costPer1M.toFixed(2)}`
  }

  const formatNumber = (num: number): string => {
    return new Intl.NumberFormat().format(num)
  }

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text)
      toast.add({
        severity: 'success',
        summary: t('litellm.copied'),
        detail: t('litellm.copiedDetail', {text}),
        life: 3000
      })
    } catch (err) {
      toast.add({
        severity: 'error',
        summary: t('litellm.copyFailed'),
        detail: t('litellm.copyFailedDetail'),
        life: 3000
      })
    }
  }

  return {
    getModeSeverity,
    formatTokenLimits,
    formatCostPer1M,
    formatNumber,
    copyToClipboard,
  }
}
