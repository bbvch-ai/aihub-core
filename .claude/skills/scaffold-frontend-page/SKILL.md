---
name: scaffold-frontend-page
description: Generate a new frontend page with Pinia-Colada composables, PrimeVue
  components, and i18n support. Creates list and detail pages following the
  established Nuxt 3 patterns.
disable-model-invocation: true
allowed-tools: Read, Write, Bash, Grep, Glob
---

# Scaffold a New Frontend Page

Generate boilerplate for a new frontend page. The page name/resource should be provided via `$ARGUMENTS`.

## Before You Start

Read the frontend scope guide: `/home/user/aihub-core/aihub_web/AGENTS.md`

Study an existing page for reference (check `aihub_web/aihub_web/pages/service/`).

## What to Generate

### 1. File Structure

```
aihub_web/aihub_web/
├── pages/service/<resource>/
│   ├── index.vue          # List page
│   └── [<resource>_id].vue  # Detail page
├── composables/
│   └── <resource>.ts      # Pinia-Colada queries and mutations
└── components/<resource>/
    └── <Resource>Card.vue  # Reusable component (optional)
```

### 2. Composable (`composables/<resource>.ts`)

Use **Pinia-Colada** patterns:

**Query (data fetching):**
```typescript
export const use<Resource>List = defineQuery(() => {
  const { data, isPending } = useQuery({
    key: () => ['<resource>s'],
    staleTime: minutesToMilliseconds(5),
    query: async () => await get<Resource>s({ composable: '$fetch' }),
  })
  return { <resource>s: data, isLoading: isPending }
})
```

**Mutation (data modification):**
```typescript
export const useCreate<Resource> = defineMutation(() => {
  const queryCache = useQueryCache()
  const { mutateAsync } = useMutation({
    mutation: async (request) => {
      await create<Resource>({ composable: '$fetch', body: request })
      queryCache.invalidateQueries({ key: ['<resource>s'] })
    },
  })
  return { create<Resource>: mutateAsync }
})
```

### 3. List Page (`pages/service/<resource>/index.vue`)

- Use `<script setup lang="ts">`
- Import composable for data fetching
- Use PrimeVue `DataTable` or card layout
- Wrap in `StructuralScreen` and `StructuralColumn`
- Use `$t('...')` for all user-visible text
- Add navigation to detail page on row click

### 4. Detail Page (`pages/service/<resource>/[<resource>_id].vue`)

- Use route params to get resource ID
- Fetch single resource with composable
- Display fields using PrimeVue components
- Include edit/delete actions if applicable

### 5. i18n

Add translation keys in all 4 locale files:
- `aihub_web/aihub_web/i18n/locales/{de,en,fr,it}.yaml`

Add keys for: page title, column headers, action labels, empty states.

### 6. Navigation

Register the new page in the sidebar navigation (if applicable).

## Key Conventions

- **PrimeVue components only**: Never raw HTML for interactive elements
- **Tailwind utility classes**: No custom CSS
- **SDK types**: Props typed from generated SDK DTOs
- **i18n all text**: `{{ $t('key.path') }}` for everything user-visible
- **Pinia-Colada**: defineQuery/defineMutation (not raw fetch)
