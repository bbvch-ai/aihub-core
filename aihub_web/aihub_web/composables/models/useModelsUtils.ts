export const useModelsUtils = () => {
  const {t} = useI18n()
  const toast = useToast()

  const getProvider = (model: any): string => {
    if (model.model_info.litellm_provider) {
      return model.model_info.litellm_provider
    }

    const modelName = model.model_name
    if (modelName.includes('azure/')) return 'azure'
    if (modelName.includes('google/') || modelName.includes('gemini')) return 'google'
    if (modelName.includes('openai/')) return 'openai'
    if (modelName.includes('anthropic/')) return 'anthropic'
    if (modelName.includes('local/')) return 'local'
    if (modelName.includes('text-embedding')) return 'openai'
    return 'unknown'
  }

  const getProviderSeverity = (provider: string): string => {
    switch (provider) {
      case 'azure':
        return 'info'
      case 'google':
        return 'success'
      case 'openai':
        return 'warn'
      case 'anthropic':
        return 'danger'
      case 'local':
        return 'secondary'
      default:
        return 'secondary'
    }
  }

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

  const formatTokenLimits = (model: any): string => {
    const input = model.model_info.max_input_tokens
    const output = model.model_info.max_output_tokens

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

  const getModelFeatures = (model: any): Array<{ name: string, severity: string }> => {
    const features: Array<{ name: string, severity: string }> = []

    if (model.model_info.supports_vision) {
      features.push({name: 'Vision', severity: 'success'})
    }

    if (model.model_info.supports_function_calling) {
      features.push({name: 'Function Calling', severity: 'info'})
    }

    if (model.model_info.supports_web_search) {
      features.push({name: 'Web Search', severity: 'help'})
    }

    if (model.model_info.supports_reasoning) {
      features.push({name: 'Reasoning', severity: 'warn'})
    }

    if (model.model_info.supports_prompt_caching) {
      features.push({name: 'Caching', severity: 'secondary'})
    }

    if (model.model_info.supports_audio_input) {
      features.push({name: 'Audio Input', severity: 'info'})
    }

    if (model.model_info.supports_audio_output) {
      features.push({name: 'Audio Output', severity: 'info'})
    }

    if (model.model_info.supports_pdf_input) {
      features.push({name: 'PDF Input', severity: 'success'})
    }

    if (model.model_info.supports_computer_use) {
      features.push({name: 'Computer Use', severity: 'danger'})
    }

    if (model.model_info.output_vector_size) {
      features.push({name: `${model.model_info.output_vector_size}D`, severity: 'secondary'})
    }

    return features
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

  const getUsageExample = (model: any): string => {
    const isImageGeneration = model.model_info.mode === 'image_generation'
    const isEmbedding = model.model_info.mode === 'embedding'

    if (isImageGeneration) {
      return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.images.generate(
    model="${model.model_name}",
    prompt="A beautiful sunset over mountains",
    size="1024x1024",
    n=1
)

print(response.data[0].url)`
    }

    if (isEmbedding) {
      return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.embeddings.create(
    model="${model.model_name}",
    input="Your text to embed here"
)

print(response.data[0].embedding)`
    }

    return `import openai

client = openai.OpenAI(
    api_key="your_api_key",
    base_url="http://0.0.0.0:4000"  # Your LiteLLM Proxy URL
)

response = client.chat.completions.create(
    model="${model.model_name}",
    messages=[
        {
            "role": "user",
            "content": "Hello, how are you?"
        }
    ]
)

print(response.choices[0].message.content)`
  }

  return {
    getProvider,
    getProviderSeverity,
    getModeSeverity,
    formatTokenLimits,
    formatCostPer1M,
    getModelFeatures,
    formatNumber,
    copyToClipboard,
    getUsageExample,
  }
}
