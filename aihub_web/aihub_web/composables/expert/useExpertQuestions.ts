import type { Ref } from 'vue'

export interface ExpertQuestionDto {
  id: string
  question: string
  context: string | null
  expert_group: string | null
  priority: 'low' | 'normal' | 'high' | 'urgent'
  locale: 'de' | 'en' | 'fr' | 'it'
  status: 'pending' | 'answered' | 'expired' | 'cancelled'
  requesting_user: {
    user_id: string
    user_name: string | null
    email: string | null
  }
  requesting_agent: {
    agent_class: string
    agent_id: string
    thread_id: string
    run_id: string
  }
  response: string | null
  responder: {
    user_id: string
    user_name: string | null
    email: string | null
    expert_group: string | null
  } | null
  responded_at: string | null
  created_at: string
  updated_at: string
}

export interface PaginatedExpertQuestionsResponse {
  total: number
  page: number
  page_size: number
  total_pages: number
  questions: ExpertQuestionDto[]
}

export const useExpertQuestions = (options: {
  currentPage: Ref<number>
  pageSize: Ref<number>
  filters?: {
    status?: Ref<string | undefined>
    expertGroup?: Ref<string | undefined>
  }
}) => {
  const { currentPage, pageSize, filters } = options
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'

  const key = () => [
    'expert-questions',
    {
      page: currentPage.value,
      pageSize: pageSize.value,
      status: filters?.status?.value,
      expertGroup: filters?.expertGroup?.value,
    },
  ]

  const query = useQuery<PaginatedExpertQuestionsResponse>({
    key,
    query: async () => {
      const params = new URLSearchParams()
      params.set('page', String(currentPage.value))
      params.set('page_size', String(pageSize.value))
      if (filters?.status?.value)
        params.set('status', filters.status.value)
      if (filters?.expertGroup?.value)
        params.set('expert_group', filters.expertGroup.value)

      const response = await $fetch<PaginatedExpertQuestionsResponse>(
        `${apiBase}/expert/questions?${params.toString()}`,
        { credentials: 'include' },
      )
      return response
    },
  })

  const questions = computed(() => query.data.value?.questions ?? [])
  const totalRecords = computed(() => query.data.value?.total ?? 0)

  return {
    questions,
    isLoading: query.isPending,
    refetch: query.refetch,
    totalRecords,
  }
}

export const usePendingExpertQuestionsCount = (expertGroup?: Ref<string | undefined>) => {
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'

  const key = () => ['expert-questions-count', { expertGroup: expertGroup?.value }]

  const query = useQuery<{ count: number }>({
    key,
    query: async () => {
      const params = new URLSearchParams()
      if (expertGroup?.value)
        params.set('expert_group', expertGroup.value)

      const response = await $fetch<{ count: number }>(
        `${apiBase}/expert/questions/pending/count?${params.toString()}`,
        { credentials: 'include' },
      )
      return response
    },
  })

  const count = computed(() => query.data.value?.count ?? 0)

  return {
    count,
    isLoading: query.isPending,
    refetch: query.refetch,
  }
}

export const useSubmitExpertAnswer = () => {
  const queryCache = useQueryCache()
  const config = useRuntimeConfig()
  const apiBase = config.public.apiUrl || '/api/v1'

  const { mutate, mutateAsync, isPending } = useMutation({
    mutation: async (params: { questionId: string, response: string, expertGroup?: string }) => {
      const queryParams = new URLSearchParams()
      if (params.expertGroup)
        queryParams.set('expert_group', params.expertGroup)

      const response = await $fetch<ExpertQuestionDto>(
        `${apiBase}/expert/questions/${params.questionId}/answer?${queryParams.toString()}`,
        {
          method: 'POST',
          credentials: 'include',
          body: { response: params.response },
        },
      )
      queryCache.invalidateQueries({ key: ['expert-questions'] })
      queryCache.invalidateQueries({ key: ['expert-questions-count'] })
      return response
    },
  })

  return { submitAnswer: mutate, submitAnswerAsync: mutateAsync, isPending }
}
