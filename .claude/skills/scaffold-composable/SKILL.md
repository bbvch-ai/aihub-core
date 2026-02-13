---
name: scaffold-composable
description: >-
  Generate Pinia-Colada composables for a backend API resource. Creates query and mutation
  composables following the established defineQuery/defineMutation patterns with SDK integration.
  Use when user says 'create a composable', 'scaffold composable', 'add query composable',
  'generate useQuery hook', 'create mutation composable', 'Pinia-Colada setup', or 'add API
  composable for resource'. Takes a resource name as argument.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Composable

Generate Pinia-Colada composables for a backend API resource. The resource name should be provided via `$ARGUMENTS`.

## Before You Start

Read the frontend scope guide: `/home/user/aihub-core/aihub_web/AGENTS.md`

Study an existing composable directory for reference:
- Simple query: `aihub_web/aihub_web/composables/agent/useAgentInstances.ts`
- Query with route params: `aihub_web/aihub_web/composables/agent/useAgentInstance.ts`
- Mutation with cache invalidation: `aihub_web/aihub_web/composables/agent/useCreateAgentInstance.ts`
- Delete mutation: `aihub_web/aihub_web/composables/agent/useDeleteAgentInstance.ts`

## Step 1: Check SDK Availability

Find the SDK functions and types for the resource in `aihub_web/aihub_web/sdk/client/`. Identify:
- **GET list**: e.g., `getAll<Resource>s`
- **GET single**: e.g., `get<Resource>`
- **POST create**: e.g., `create<Resource>`
- **PUT update**: e.g., `update<Resource>`
- **DELETE**: e.g., `delete<Resource>`
- **DTO types**: e.g., `Full<Resource>Dto`, `Create<Resource>Request`

If SDK functions don't exist yet, warn the user to run `/generate-sdk` first.

## Step 2: Create Composable Directory

```
aihub_web/aihub_web/composables/<resource>/
├── use<Resource>s.ts              # List query (GET all)
├── use<Resource>.ts               # Single item query (GET by ID)
├── useCreate<Resource>.ts         # Create mutation (POST)
├── useUpdate<Resource>.ts         # Update mutation (PUT)
└── useDelete<Resource>.ts         # Delete mutation (DELETE)
```

Only create files for SDK operations that actually exist.

## Step 3: List Query Pattern

```typescript
import { type Full<Resource>Dto, getAll<Resource>s } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const use<Resource>s = defineQuery(() => {
  const { data: <resource>s, isPending: <resource>sAreLoading } = useQuery<Full<Resource>Dto[]>({
    key: () => ['<resource>s'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAll<Resource>s({ composable: '$fetch' })
    },
  })
  return {
    <resource>s,
    <resource>sAreLoading,
  }
})
```

## Step 4: Single Item Query Pattern (with route params)

```typescript
import { type Full<Resource>Dto, get<Resource> } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const use<Resource> = defineQuery(() => {
  const route = useRoute()
  const isRouteReady = useRouteReady('<resource>_id')

  const { data: <resource>, isPending: <resource>IsLoading } = useQuery<Full<Resource>Dto>({
    key: () => ['<resource>s', route.params.<resource>_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: isRouteReady,
    query: async () => {
      return await get<Resource>({
        composable: '$fetch',
        path: { <resource>_id: route.params.<resource>_id as string },
      })
    },
  })
  return {
    <resource>,
    <resource>IsLoading,
  }
})
```

## Step 5: Mutation Pattern (create/update/delete)

```typescript
import { type Create<Resource>Request, create<Resource> } from '@core/sdk/client'
import { useMutation, useQueryCache } from '@pinia/colada'

export const useCreate<Resource> = defineMutation(() => {
  const queryCache = useQueryCache()
  const {
    mutateAsync: create<Resource>Mutation,
    isPending: isCreating,
    error: createError,
  } = useMutation({
    mutation: async (request: Create<Resource>Request) => {
      const result = await create<Resource>({
        composable: '$fetch',
        body: request,
      })
      queryCache.invalidateQueries({ key: ['<resource>s'] })
      return result
    },
  })
  return {
    create<Resource>: create<Resource>Mutation,
    isCreating,
    createError,
  }
})
```

## Examples

**Typical invocation**: `/scaffold-composable pipeline`

**Result**: Creates composable files in `aihub_web/aihub_web/composables/pipeline/`:
- `usePipelines.ts` — list query
- `usePipeline.ts` — single item query with route params
- `useCreatePipeline.ts` — create mutation with cache invalidation
- `useDeletePipeline.ts` — delete mutation

## Troubleshooting

| Problem | Solution |
|---------|----------|
| SDK functions not found | Run `/generate-sdk` first to regenerate the client SDK |
| Query never resolves | Check `enabled` flag — use `useRouteReady()` for route-dependent queries |
| Stale data after mutation | Ensure `queryCache.invalidateQueries({ key: ['resources'] })` is called |
| Type errors on DTO imports | Regenerate SDK — types may be outdated |
| Composable not auto-imported | Nuxt auto-imports from `composables/` — ensure file is in the right directory |

## Key Conventions

- **`{ composable: '$fetch' }`**: Always pass this to SDK calls (uses Nuxt's `$fetch`)
- **Query keys**: Hierarchical arrays `['<resource>s']`, `['<resource>s', id]`
- **`staleTime`**: Use `minutesToMilliseconds(5)` for standard resources
- **`enabled`**: Use `useRouteReady()` when query depends on route params
- **Cache invalidation**: Call `queryCache.invalidateQueries({ key: ['<resource>s'] })` after mutations
- **Naming**: `use<Resource>s` (plural list), `use<Resource>` (single), `useCreate<Resource>` (mutation)
- **Exports**: Always wrap in `defineQuery()` or `defineMutation()` (Pinia-Colada composable factories)
- **Types**: Import DTO types from `@core/sdk/client`, never define manually
