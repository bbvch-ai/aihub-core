import { searchMemories, type MemorySearchResponse } from '@core/sdk/client'
import { defineQuery } from '@pinia/colada'
import { ref } from 'vue'

export const useMemorySearch = defineQuery(() => {
  const query = ref<string>('')
  const limit = ref(100)
  const agentId = ref<string | undefined>(undefined)
  const threadId = ref<string | undefined>(undefined)

  const { data, isPending } = useQuery<MemorySearchResponse>({
    key: () => ['memory-search', { query: query.value, limit: limit.value, agentId: agentId.value, threadId: threadId.value }],
    staleTime: 1000 * 30,
    enabled: () => !!query.value,
    query: async () => {
      if (!query.value) {
        return {
          query: '',
          total: 0,
          memories: [],
          relations: [],
        }
      }

      const response = await searchMemories({
        query: {
          query: query.value,
          limit: limit.value,
          agent_id: agentId.value,
          thread_id: threadId.value,
        },
      })
      return response.data as MemorySearchResponse
    },
  })

  const setSearchQuery = (q: string) => {
    query.value = q
  }

  const setAgentFilter = (id: string | undefined) => {
    agentId.value = id
  }

  const setThreadFilter = (id: string | undefined) => {
    threadId.value = id
  }

  const clearSearch = () => {
    query.value = ''
  }

  return {
    data,
    isPending,
    query,
    limit,
    agentId,
    threadId,
    setSearchQuery,
    setAgentFilter,
    setThreadFilter,
    clearSearch,
  }
})
