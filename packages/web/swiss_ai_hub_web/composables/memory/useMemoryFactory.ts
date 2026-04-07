import {
  getUserMemories,
  searchUserMemories,
  updateUserMemory,
  deleteUserMemory,
  deleteAllUserMemories,
  getOrganizationMemories,
  searchOrganizationMemories,
  updateOrganizationMemory,
  deleteOrganizationMemory,
  deleteAllOrganizationMemories,
} from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { computed, ref } from 'vue'

import type { MemoriesResponse, MemorySearchResponse } from '@core/sdk/client'

type MemoryType = 'user' | 'organization'

interface MemoryContext {
  type: MemoryType
  agent_class?: string
  agent_id?: string
  thread_id?: string
}

/**
 * Factory function to create memory composables for both user and organization memory types.
 * This eliminates code duplication by generating type-specific hooks from a single implementation.
 *
 * @param context - Memory context specifying type (user/organization)
 * @returns Object containing all memory-related composables
 *
 * @example
 * // User memory
 * const { useMemories, useMemorySearch } = createMemoryComposables({ type: 'user' })
 *
 * @example
 * // Organization memory (tenant from env-var)
 * const { useMemories, useMemorySearch } = createMemoryComposables({ type: 'organization' })
 */
export function createMemoryComposables(context: MemoryContext) {
  const { type, agent_class, agent_id, thread_id } = context

  /**
   * Generate cache keys with proper scoping for user vs organization memory
   */
  const getCacheKey = (operation: string, params: Record<string, unknown> = {}) => {
    const baseParams = { ...params, agent_class, agent_id, thread_id }
    if (type === 'user') {
      return ['memories', 'user', operation, baseParams]
    }
    return ['memories', 'organization', operation, baseParams]
  }

  /**
   * Composable for fetching and paginating memories
   */
  const useMemories = defineQuery(() => {
    const { tenantName } = useTenantFromRoute()
    const currentPage = ref(1)
    const pageSize = ref(20)

    const {
      data: memoriesData,
      isPending: memoriesAreLoading,
    } = useQuery<MemoriesResponse>({
      key: () => getCacheKey('list', { tenant: tenantName.value, page: currentPage.value }),
      staleTime: minutesToMilliseconds(5),
      enabled: computed(() => !!tenantName.value),
      query: async () => {
        // Use search endpoint when filters are provided (agent_class/agent_id/thread_id)
        const hasFilters = agent_class || agent_id || thread_id

        if (type === 'user') {
          if (hasFilters) {
            // Search endpoint supports filtering
            return await searchUserMemories({
              composable: '$fetch',
              path: { tenant_id: tenantName.value! },
              query: {
                query: '', // Empty query returns all memories
                limit: 1000,
                agent_class: agent_class || null,
                agent_id: agent_id || null,
                thread_id: thread_id || null,
              },
            })
          }
          return await getUserMemories({
            composable: '$fetch',
            path: { tenant_id: tenantName.value! },
            query: { limit: 1000 },
          })
        }

        if (hasFilters) {
          return await searchOrganizationMemories({
            composable: '$fetch',
            path: { tenant_id: tenantName.value! },
            query: {
              query: '', // Empty query returns all memories
              limit: 1000,
              agent_class: agent_class || null,
              agent_id: agent_id || null,
              thread_id: thread_id || null,
            },
          })
        }
        return await getOrganizationMemories({
          composable: '$fetch',
          path: { tenant_id: tenantName.value! },
          query: {
            limit: 1000,
          },
        })
      },
    })

    const paginatedMemories = computed(() => {
      if (!memoriesData.value) return []
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return memoriesData.value.memories.slice(start, end)
    })

    const totalPages = computed(() => {
      if (!memoriesData.value) return 0
      return Math.ceil(memoriesData.value.memories.length / pageSize.value)
    })

    const allRelations = computed(() => {
      return memoriesData.value?.relations || []
    })

    const nextPage = () => {
      if (currentPage.value < totalPages.value) {
        currentPage.value++
      }
    }

    const prevPage = () => {
      if (currentPage.value > 1) {
        currentPage.value--
      }
    }

    return {
      memoriesData,
      memoriesAreLoading,
      paginatedMemories,
      allRelations,
      currentPage,
      pageSize,
      totalPages,
      nextPage,
      prevPage,
    }
  })

  /**
   * Composable for semantic memory search
   */
  const useMemorySearch = defineQuery(() => {
    const { tenantName } = useTenantFromRoute()
    const query = ref<string>('')
    const limit = ref(100)

    const {
      data: searchData,
      isPending: searchIsLoading,
    } = useQuery<MemorySearchResponse>({
      key: () => getCacheKey('search', { tenant: tenantName.value, query: query.value, limit: limit.value }),
      staleTime: minutesToMilliseconds(1),
      enabled: () => !!query.value && !!tenantName.value,
      query: async () => {
        if (type === 'user') {
          return await searchUserMemories({
            composable: '$fetch',
            path: { tenant_id: tenantName.value! },
            query: {
              query: query.value,
              limit: limit.value,
              agent_class: agent_class || null,
              agent_id: agent_id || null,
              thread_id: thread_id || null,
            },
          })
        }

        return await searchOrganizationMemories({
          composable: '$fetch',
          path: { tenant_id: tenantName.value! },
          query: {
            query: query.value,
            limit: limit.value,
            agent_class: agent_class || null,
            agent_id: agent_id || null,
            thread_id: thread_id || null,
          },
        })
      },
    })

    const isSearchActive = computed(() => !!query.value)

    const setSearchQuery = (q: string) => {
      query.value = q
    }

    const clearSearch = () => {
      query.value = ''
    }

    return {
      searchData,
      searchIsLoading,
      query,
      isSearchActive,
      setSearchQuery,
      clearSearch,
    }
  })

  /**
   * Composable for updating memory content
   */
  const useUpdateMemory = defineMutation(() => {
    const queryCache = useQueryCache()

    const { mutate: updateMemoryMutation } = useMutation({
      mutation: async ({ memoryId, data, tenantId }: { memoryId: string, data: string, tenantId: string }) => {
        if (type === 'user') {
          await updateUserMemory({
            composable: '$fetch',
            path: { tenant_id: tenantId, memory_id: memoryId },
            body: { data },
          })
        }
        else {
          await updateOrganizationMemory({
            composable: '$fetch',
            path: { tenant_id: tenantId, memory_id: memoryId },
            body: { data },
          })
        }

        // Invalidate cache to trigger refetch
        queryCache.invalidateQueries({ key: getCacheKey('list') })
      },
    })

    return { updateMemory: updateMemoryMutation }
  })

  /**
   * Composable for deleting memories
   */
  const useDeleteMemory = defineMutation(() => {
    const queryCache = useQueryCache()

    const { mutate: deleteMemoryMutation } = useMutation({
      mutation: async ({ memoryId, tenantId }: { memoryId: string, tenantId: string }) => {
        if (type === 'user') {
          await deleteUserMemory({
            composable: '$fetch',
            path: { tenant_id: tenantId, memory_id: memoryId },
          })
        }
        else {
          await deleteOrganizationMemory({
            composable: '$fetch',
            path: { tenant_id: tenantId, memory_id: memoryId },
          })
        }

        // Invalidate cache to trigger refetch
        queryCache.invalidateQueries({ key: getCacheKey('list') })
      },
    })

    const { mutate: deleteAllMemoriesMutation } = useMutation({
      mutation: async ({ tenantId }: { tenantId: string }) => {
        if (type === 'user') {
          await deleteAllUserMemories({
            composable: '$fetch',
            path: { tenant_id: tenantId },
          })
        }
        else {
          await deleteAllOrganizationMemories({
            composable: '$fetch',
            path: { tenant_id: tenantId },
          })
        }

        // Invalidate both list and search cache
        queryCache.invalidateQueries({ key: getCacheKey('list') })
        queryCache.invalidateQueries({ key: getCacheKey('search') })
      },
    })

    return {
      deleteMemory: deleteMemoryMutation,
      deleteAllMemories: deleteAllMemoriesMutation,
    }
  })

  return {
    useMemories,
    useMemorySearch,
    useUpdateMemory,
    useDeleteMemory,
  }
}
