---
name: audit-frontend
description: Run a comprehensive frontend code audit of the Nuxt 3 admin interface. Checks Pinia-Colada query/mutation patterns, TypeScript strictness, component architecture, SDK freshness, i18n coverage, and Tailwind usage. Use when user says 'audit the frontend', 'check frontend code quality', 'find unused components', 'composable health check', 'pinia-colada audit', 'typescript errors', or 'frontend code review'. Do NOT use for backend API audits (use scaffold-api-endpoint) or bot UI issues (use debug-bot). Reports issues with file locations and severity levels.
allowed-tools: Read, Bash, Grep, Glob
---

# Frontend Code Audit

Run a comprehensive audit of the Nuxt 3 admin interface at `packages/web/aihub_web/`. Scope via `$ARGUMENTS`: `all`,
`composables`, `typescript`, `components`, `pages`, `sdk`, `i18n`, `tailwind`.

Default scope is `all` if no argument provided.

Before starting, read `packages/web/CLAUDE.md` for the full frontend conventions reference.

______________________________________________________________________

## Audit 1: Pinia-Colada Composables (scope: `composables`)

Check all files in `packages/web/aihub_web/composables/` against these rules:

### 1a. defineQuery/defineMutation wrappers (ERROR)

Every exported query composable must use `defineQuery()`, every mutation must use `defineMutation()`. Bare `useQuery` or
`useMutation` in a plain exported function is an anti-pattern — it breaks singleton caching.

```bash
# Find bare useQuery not wrapped in defineQuery
grep -rn "export.*=.*(" packages/web/aihub_web/composables/ --include="*.ts" | grep -v defineQuery | grep -v defineMutation
```

Cross-check: if a file imports `useQuery` from `@pinia/colada` but doesn't call `defineQuery`, flag it.

### 1b. Query keys must be functions (ERROR)

Keys must be arrow functions `key: () => [...]`, never static arrays `key: [...]`. Static keys don't react to route or
ref changes.

```bash
# Find static query keys (array literal without arrow function)
grep -rn "key: \[" packages/web/aihub_web/composables/ --include="*.ts"
```

Correct: `key: () => ['agent-instances', route.params.agent_class]` Wrong:
`key: ['agent-instances', route.params.agent_class]`

### 1c. staleTime must use minutesToMilliseconds (ERROR)

Every `useQuery` must have `staleTime: minutesToMilliseconds(N)` (from `date-fns`). Standard is 5 minutes. Missing
`staleTime` means the global default applies, which may not be intentional.

```bash
# Find useQuery calls without staleTime
grep -rn "useQuery" packages/web/aihub_web/composables/ --include="*.ts" -A 5 | grep -v staleTime
```

Hardcoded milliseconds like `staleTime: 300000` are also wrong — use the `date-fns` helper.

### 1d. composable: '\$fetch' on every SDK call (ERROR)

Every SDK function call must include `composable: '$fetch'` — this is required by the `@hey-api/client-nuxt` adapter.
Missing it causes the request to use raw `fetch` instead of Nuxt's `$fetch`, breaking auth token injection.

```bash
# Find SDK calls without composable: '$fetch'
grep -rn "await \(get\|create\|update\|delete\|post\|put\|patch\)" packages/web/aihub_web/composables/ --include="*.ts"
```

Cross-check each SDK call has `composable: '$fetch'` in its options object.

### 1e. Route-dependent queries must use useRouteReady (WARNING)

If a query uses `route.params.*`, it must have `enabled: useRouteReady('param_name')` to prevent firing before the route
resolves. During route transitions, params can briefly be template placeholders like `'{agent_id}'`.

Reference implementation: `packages/web/aihub_web/composables/useRouteReady.ts`

### 1f. Mutations must invalidate query cache (WARNING)

Every mutation should call `queryCache.invalidateQueries()` — either inside the mutation function or in `onSettled`.
Prefer `onSettled` over `onSuccess` for cache invalidation (runs regardless of success/failure). Mutations should
invalidate both broad keys (`['agents']`) and specific keys (`['agents', agentClass, agentId]`).

### 1g. Named exports, not default (WARNING)

Composables must use `export const useFoo = defineQuery(...)`, not `export default defineQuery(...)`. Default exports
lose the explicit name and rely on filename inference for auto-import.

```bash
# Find default exports in composables
grep -rn "export default" packages/web/aihub_web/composables/ --include="*.ts"
```

### 1h. Query key naming conventions (WARNING)

Keys should be kebab-case string arrays: `['agent-classes']`, `['agent-instances', agentClass, agentId]`. Check for:

- Snake_case keys (`['my_user']` should be `['my-user']`)
- Keys that don't include all reactive inputs used in the query function

______________________________________________________________________

## Audit 2: TypeScript Strictness (scope: `typescript`)

### 2a. Untyped function parameters (ERROR)

Find callback parameters without type annotations (implicit `any`).

```bash
# Find untyped arrow function params in .vue and .ts files
grep -rn "=> {" packages/web/aihub_web/pages/ packages/web/aihub_web/components/ --include="*.vue" --include="*.ts" | grep "(event)" | grep -v ": "
```

Common offender: `const handleClick = (event) => {` should be `(event: MouseEvent) => {`.

### 2b. Type imports must use `import type` (WARNING)

SDK types should use `import type { FooDto }` not `import { FooDto }`. Regular imports pull in runtime code; type
imports are erased at compile time.

```bash
# Find non-type imports of SDK types (Dto suffix = type)
grep -rn "import {.*Dto" packages/web/aihub_web/ --include="*.vue" --include="*.ts" | grep -v "import type"
```

Exception: types re-exported as values (e.g., `export type AgentClassDto = AgentClassDtoReadable`) are fine.

### 2c. Route params must be cast (WARNING)

`route.params.foo` is `string | string[]`. Always cast to `string` when passing to SDK functions:
`route.params.agent_id as string`. Flag bare `route.params.foo` passed directly to functions without cast.

### 2d. Computed vs function naming (WARNING)

Computed refs named with `get` prefix (like `getEmptyStateTitle = computed(...)`) suggest a function but are reactive
refs. Either name them as nouns (`emptyStateTitle`) or make them actual functions.

### 2e. console.log in production code (WARNING)

```bash
grep -rn "console\.\(log\|debug\|info\)" packages/web/aihub_web/ --include="*.vue" --include="*.ts" \
  | grep -v "node_modules" | grep -v "sdk/"
```

`console.error` in global error handlers (`app.vue`) is acceptable. `console.log` in pages/components is not.

______________________________________________________________________

## Audit 3: Component Architecture (scope: `components`)

### 3a. Unused components (WARNING)

```bash
# For each .vue file in components/, derive auto-import name and search for usage
find packages/web/aihub_web/components/ -name "*.vue" | while read f; do
  # Agent/Card.vue → AgentCard
  NAME=$(echo "$f" | sed 's|.*/components/||; s|\.vue$||; s|/||g')
  USAGE=$(grep -rl "$NAME" packages/web/aihub_web/ --include="*.vue" --include="*.ts" | grep -v "$f" | wc -l)
  [ "$USAGE" -eq 0 ] && echo "UNUSED: $f ($NAME)"
done
```

### 3b. Props/emits typing pattern (WARNING)

Components should use:

- `withDefaults(defineProps<{...}>(), {...})` for props with defaults
- `defineEmits<{ eventName: [argType] }>()` for typed emits (Vue 3.3+ named tuple form)
- `defineProps<{...}>()` for props without defaults

Flag components using the options API syntax (`props: { ... }`) or untyped `defineEmits(['click'])`.

### 3c. v-model bridging pattern (INFO)

For `v-model` on custom components, check for the standard pattern:

```typescript
const visible = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value),
})
```

Flag cases where `modelValue` prop exists but the writable computed bridge is missing.

### 3d. Dark mode completeness (WARNING)

Every `bg-surface-*`, `text-surface-*`, `border-surface-*` class should have a `dark:` variant pair:

- Light: `bg-surface-50/100/200`, Dark: `dark:bg-surface-800/900/950`
- Light: `text-surface-500/600/700`, Dark: `dark:text-surface-300/400`
- Light: `border-surface-200/300`, Dark: `dark:border-surface-700/800`

```bash
# Find surface classes without dark: companion on the same element
grep -rn "bg-surface-\(50\|100\|200\)" packages/web/aihub_web/components/ --include="*.vue" \
  | grep -v "dark:bg-surface"
```

______________________________________________________________________

## Audit 4: Page Architecture (scope: `pages`)

### 4a. StructuralScreen/Column pattern (ERROR)

List pages must follow:

```
StructuralScreen > StructuralColumn + NuxtPage
```

Check that every file directly under `pages/service/*.vue` wraps content in `StructuralScreen` with a `NuxtPage` for
detail routing.

```bash
grep -rL "StructuralScreen" packages/web/aihub_web/pages/service/*.vue
```

### 4b. localePath for all navigation (ERROR)

All `router.push()`, `navigateTo()`, and `NuxtLink :to` must use `localePath()`. Bare paths like
`router.push('/service/agents')` break i18n locale prefixing.

```bash
# Find bare path navigation without localePath
grep -rn "router\.push\|navigateTo" packages/web/aihub_web/pages/ packages/web/aihub_web/components/ --include="*.vue" \
  | grep -v localePath | grep -v "//.*router"
```

Also check `<NuxtLink :to="` attributes — they should wrap paths in `localePath()`.

### 4c. NavItem isActive must be a closure (ERROR)

In hub pages (e.g., `[agent_class]-[agent_id].vue`), `NavItem.isActive` must be a **function returning boolean**, not a
boolean value. The `SelectButton` calls `isActive()` dynamically.

```typescript
// Correct: closure
isActive: () => route.path.startsWith(localePath(subPath('overview')))
// Wrong: evaluated once
isActive: route.path.startsWith(localePath(subPath('overview')))
```

### 4d. Detail pages use close-route (WARNING)

Leaf pages (inside `[param]/`) should pass `close-route` to `StructuralColumn` for the back button. The path should be
bare (not wrapped in `localePath` — `StructuralColumn` applies it internally).

### 4e. Unnecessary explicit imports (WARNING)

In `<script setup>`, these are auto-imported and must NOT be explicitly imported:

- Vue: `ref`, `computed`, `watch`, `onMounted`, `nextTick`
- Vue Router: `useRoute`, `useRouter`, `navigateTo`
- i18n: `useI18n`
- PrimeVue: `useConfirm`, `useToast`
- All composables from `composables/` and `composables/**/`

```bash
# Find unnecessary imports in pages and components
grep -rn "import.*from 'vue'" packages/web/aihub_web/pages/ packages/web/aihub_web/components/ --include="*.vue"
grep -rn "import.*from 'vue-router'" packages/web/aihub_web/pages/ --include="*.vue"
grep -rn "import.*from 'vue-i18n'" packages/web/aihub_web/pages/ --include="*.vue"
grep -rn "import.*from 'primevue/use" packages/web/aihub_web/pages/ --include="*.vue"
```

Exception: `useLocalePath` from `'#i18n'` DOES need explicit import.

______________________________________________________________________

## Audit 5: SDK Freshness (scope: `sdk`)

1. Check if API is accessible:

```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/openapi.json
```

2. If accessible, compare OpenAPI spec endpoints with `packages/web/aihub_web/sdk/client/sdk.gen.ts`:

   - Report: new endpoints missing from SDK, removed endpoints still in SDK

3. If not accessible, compare timestamps of SDK files vs latest `packages/api/` changes:

```bash
stat -c %Y packages/web/aihub_web/sdk/client/sdk.gen.ts
git log -1 --format=%ct packages/api/
```

4. Verify SDK is never manually edited — check git status for modifications in `sdk/client/`.

______________________________________________________________________

## Audit 6: i18n Coverage (scope: `i18n`)

1. Read all locale files: `packages/web/aihub_web/i18n/locales/{de,en,fr,it}.yaml`
2. Use English as reference — find keys missing in de/fr/it
3. Find keys in de/fr/it that don't exist in en (orphaned)
4. Check for empty string values
5. Scan `.vue` files for `$t('...')` and `t('...')` calls — find keys used in code but missing from en.yaml
6. Report coverage per language as a percentage

Note: some keys are dynamically constructed with template literals — flag them as unverifiable, not missing.

______________________________________________________________________

## Audit 7: Tailwind and Styling (scope: `tailwind`)

### 7a. Style blocks should be minimal (WARNING)

`<style>` blocks are acceptable only for PrimeVue deep overrides (`:deep(.p-panel-header)`). Flag large style blocks
(more than 10 lines) or style blocks not using `:deep()` — they should use Tailwind classes instead.

```bash
# Find style blocks and count lines
grep -rn "<style" packages/web/aihub_web/components/ packages/web/aihub_web/pages/ --include="*.vue"
```

### 7b. Inline styles (WARNING)

```bash
grep -rn 'style="' packages/web/aihub_web/components/ packages/web/aihub_web/pages/ --include="*.vue" | grep -v ":style"
```

Static `style=""` should be Tailwind classes. Dynamic `:style` for computed values is acceptable.

### 7c. PrimeVue surface tokens (INFO)

Verify that surface color tokens use PrimeVue semantic names (`surface-50` through `surface-950`) rather than Tailwind
gray/slate/zinc (`gray-100`, `slate-200`). PrimeVue surface tokens respect the theme.

```bash
grep -rn "text-\(gray\|slate\|zinc\|neutral\|stone\)-" packages/web/aihub_web/ --include="*.vue"
grep -rn "bg-\(gray\|slate\|zinc\|neutral\|stone\)-" packages/web/aihub_web/ --include="*.vue"
```

______________________________________________________________________

## Report Format

Present findings as a summary table:

| Audit Area       | Status         | Issues Found | Severity |
| ---------------- | -------------- | ------------ | -------- |
| Composables      | pass/warn/fail | Count        | High     |
| TypeScript       | pass/warn/fail | Count        | High     |
| Components       | pass/warn      | Count        | Medium   |
| Pages            | pass/warn/fail | Count        | High     |
| SDK Freshness    | pass/warn/fail | Count        | Medium   |
| i18n Coverage    | pass/warn/fail | Count + %    | Medium   |
| Tailwind/Styling | pass/warn      | Count        | Low      |

Then list each issue grouped by audit area with: file path, line number, issue description, suggested fix.

## Examples

- `/audit-frontend all` -- Run all 7 audits and produce summary table
- `/audit-frontend composables` -- Deep check on Pinia-Colada patterns (defineQuery, keys, staleTime, cache)
- `/audit-frontend typescript` -- Find type errors, implicit any, missing type imports
- `/audit-frontend pages` -- Check page architecture, localePath usage, NavItem patterns
- `/audit-frontend i18n` -- Cross-check translation keys across de/en/fr/it locales

## Troubleshooting

| Issue                                  | Resolution                                                               |
| -------------------------------------- | ------------------------------------------------------------------------ |
| API unreachable for SDK check          | Skip SDK freshness audit, report as "skipped (API unreachable)"          |
| Too many unused components             | Verify auto-import naming: `Agent/Card.vue` becomes `AgentCard`          |
| False positive on i18n keys            | Some keys are dynamically constructed — check for template literals      |
| Composable uses bare `useQuery`        | Flag as ERROR — should be wrapped in `defineQuery` for singleton caching |
| `useLocalePath` flagged as unnecessary | This IS required — it must be imported from `'#i18n'`                    |
