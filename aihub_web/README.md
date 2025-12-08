---
title: AI-Hub Frontend
index: 8
---

# AI-Hub Web Frontend Developer's Guide

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_aihub-web&metric=alert_status&token=2544c19db5da47510d04d7ee0694f364127a21e0)](https://sonarcloud.io/summary/new_code?id=aihub-core_aihub-web)

[![Security Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_aihub-web&metric=security_rating&token=2544c19db5da47510d04d7ee0694f364127a21e0)](https://sonarcloud.io/summary/new_code?id=aihub-core_aihub-web)

[![Vulnerabilities](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_aihub-web&metric=vulnerabilities&token=2544c19db5da47510d04d7ee0694f364127a21e0)](https://sonarcloud.io/summary/new_code?id=aihub-core_aihub-web)

[![Maintainability Rating](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_aihub-web&metric=sqale_rating&token=2544c19db5da47510d04d7ee0694f364127a21e0)](https://sonarcloud.io/summary/new_code?id=aihub-core_aihub-web)

[![Lines of Code](https://sonarcloud.io/api/project_badges/measure?project=aihub-core_aihub-web&metric=ncloc&token=2544c19db5da47510d04d7ee0694f364127a21e0)](https://sonarcloud.io/summary/new_code?id=aihub-core_aihub-web)

You are contributing to the **aihub_web** scope, which contains the main web frontend application within the AI-Hub
platform. This scope implements the user interface that connects users to AI agents, processes, and system management
capabilities through an intuitive, modern web application built with Nuxt 3.

## The Stack

Our frontend is built on a modern, type-safe, and efficient technology stack. Below is a breakdown of the core
frameworks, libraries, and tools we use.

### Core Framework

- **[Nuxt 3](https://nuxt.com/)**: The core application framework, built on top of Vue 3.
- **[Vue 3](https://vuejs.org/)**: The progressive JavaScript framework for building user interfaces.

### UI & Styling

- **[PrimeVue](https://primevue.org/)**: Our primary component library for rich UI components.
- **[Tailwind CSS](https://tailwindcss.com/)**: A utility-first CSS framework for rapid styling.
- **Icons**:
  - **[PrimeIcons](https://primevue.org/icons/)**: The default icon library for PrimeVue.
  - **[@nuxt/icon](https://github.com/nuxt/icon)**: Leveraging the extensive **[Iconify](https://iconify.design/)**
    collection for a wide variety of icons.

### State Management

- **[Pinia Colada](https://pinia-colada.esm.dev/)**: Used to map API state directly to reactive Vue state, avoiding the
  need for a global Pinia store.

### Backend Communication

- **REST API**: We consume our backend via a RESTful API.
  - **[Hey API](https://heyapi.dev/)**: Used to auto-generate a type-safe TypeScript SDK for our API.
- **[Socket.IO](https://socket.io/)**: For establishing real-time, bi-directional communication with the backend.

### Utilities

- **[VueUse](https://vueuse.org/)**: A collection of essential Composition API utilities.
- **[lodash](https://lodash.com/)**: For advanced utility functions. We install sub-packages individually (e.g.,
  `lodash.clonedeep`) to keep the bundle size small.
- **[date-fns](https://date-fns.org/)**: A modern and lightweight library for date manipulation.

### Data Visualization

- **[ApexCharts](https://apexcharts.com/)**: Our charting library for creating interactive data visualizations.

### Code Quality

- **[TypeScript](https://www.typescriptlang.org/)**: Our entire codebase is written in TypeScript, ensuring type safety.
- **[ESLint](https://eslint.org/)**: We enforce a strict linting configuration to maintain high code quality and
  consistency.

## Project Structure

The `aihub_web` scope is organized as follows:

```
aihub_web/
├── aihub_web/                 # Main application source
│   ├── components/            # Vue components organized by domain
│   │   ├── Agent/             # Agent-related components
│   │   ├── Chat/              # Chat interface components
│   │   ├── Dashboard/         # Dashboard and analytics components
│   │   ├── Event/             # Event display and management
│   │   ├── Navigation/        # Navigation and layout components
│   │   ├── Process/           # Process management interface
│   │   ├── Thread/            # Thread management components
│   │   └── ...                # Other domain-specific components
│   ├── composables/           # Vue composables for state management
│   │   ├── agent/             # Agent-related composables
│   │   ├── auth/              # Authentication composables
│   │   ├── chat/              # Chat functionality
│   │   ├── evaluation/        # Evaluation and testing
│   │   ├── thread/            # Thread management
│   │   └── ...                # Other domain composables
│   ├── pages/                 # File-based routing pages
│   │   ├── service/           # Main service pages
│   │   │   ├── agents/        # Agent management pages
│   │   │   ├── processes/     # Process management pages
│   │   │   ├── threads/       # Thread management pages
│   │   │   └── ...            # Other service pages
│   │   └── auth/              # Authentication pages
│   ├── layouts/               # Application layouts
│   ├── middleware/            # Route middleware
│   ├── plugins/               # Nuxt plugins
│   ├── sdk/                   # Generated API client SDK
│   ├── i18n/                  # Internationalization files
│   └── themes/                # Custom PrimeVue themes
├── package.json               # Dependencies and scripts
├── nuxt.config.ts             # Nuxt configuration
├── tailwind.config.mjs        # Tailwind CSS configuration
└── eslint.config.js           # ESLint configuration
```

## The Component Architecture

The frontend follows a component-based architecture with clear separation of concerns between pages, components and
composables.

::: code-group
```vue [pages/service/agents.vue]
<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="agentsAreLoading"
    >
      <div
        class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
      >
        <AgentCard
          v-for="agent in agents"
          :key="agent.agent_id"
          :agent="agent"
          @click="() => toAgent(agent)"
        />
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { agents, agentsAreLoading } = useAgents()

const toAgent = (agent: AgentDto) => {
  router.push(localePath(`/service/agents/agent-${agent.agent_id}-${agent.agent_class}/overview`))
}
</script>
```

```vue [components/Agent/Card.vue]
<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    :class="{ 'bg-surface-100 dark:bg-surface-800': isActive }"
  >
    <div class="flex items-center justify-between gap-4">
      ...
    </div>
  </div>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

const props = defineProps<{
  agent: AgentDto
}>()

const route = useRoute()
const { t } = useI18n()

const isActive = computed(() => {
  return route.params.agent_id === props.agent.agent_id && route.params.agent_class === props.agent.agent_class
})
</script>

```

```ts [composables/agent/useAgents.ts]
import { type AgentDto, getAgents } from '@core/sdk/client'
import { useQuery } from '@pinia/colada'
import { minutesToMilliseconds } from 'date-fns'

export const useAgents = defineQuery(() => {
  const { data: agents, isPending: agentsAreLoading } = useQuery<AgentDto[]>({
    key: () => ['agents'],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getAgents({
        composable: '$fetch',
      })
    },
  })
  return {
    agents,
    agentsAreLoading,
  }
})

```
:::

**Key Principles:**

- **Service-Driven:** For each API service endpoint (like `agent`, `user`, `process`, `role`, ...), there is a frontend
  service
- **Pages:** For each service, there is a page that is called exactly the same as the service.
- **Components:** For each service, there is a component folder containing the vue components for said service
- **Composable:** To interact with the service, for each endpoint, there is a composable wrapping that endpoint into
  state using pinia-colada

## Client SDK generation

We use `hey-api` to automatically generate a client side SDK from our API endpoints. This allows us to use our API
endpoints like functions and have full typing.

You can import types from `@core/sdk/client`

```ts{1,3,7}
import Avatar from 'primevue/avatar'

import type { AgentDto, MinimalAgentDto } from '@core/sdk/client'

withDefaults(defineProps<{
  size?: 'normal' | 'large'
  agent: AgentDto | MinimalAgentDto
}>(), {
  size: 'large',
})
```

Similarly, you can import the endpoints from `@core/sdk/client`

```ts{1,3-9}
import { type AgentDto, getAgent } from '@core/sdk/client'

await getAgent({
  composable: '$fetch',
  path: {
    agent_id: route.params.agent_id as string,
    agent_class: route.params.agent_class as string,
  },
})
```

## State Management with Pinia-Colada

We use pinia-colda for mapping api operations to states: GET map to query, PUT, PATCH, POST and DELETE map to mutation.
We use keys to auto-invalidate queries when new data is posted.

### Getting State

Using the client SDK and pinia-colada, we can define a role like a state. Instead of explicitly **calling** the API or
the client sdk function, we **define** the state that the composable should hold, and let pinia-colada handle the
fetching logic for us.

In the example below, we fetch a role based on its ID. As the ID is conveniently part of the route, the composable
automatically **depends** on the reactive route parameter.

Hence, when the browser route changes, the `route.params.role_id` changes as well, triggering pinia-colada to re-fetch
the role and update the state, taking care of caching and refreshing.

::: code-group
```ts [useRole.ts]
import { getRole, type RoleResponse } from '@core/sdk/client'
import { minutesToMilliseconds } from 'date-fns'
import { useRoute } from 'vue-router'

export default defineQuery(() => {
  const route = useRoute()

  const {
    data: role,
    isPending: roleIsLoading,
  } = useQuery<RoleResponse>({
    key: () => ['roles', route.params.role_id as string],
    staleTime: minutesToMilliseconds(5),
    enabled: true,
    query: async () => {
      return await getRole({
        composable: '$fetch',
        path: {
          role_id: route.params.role_id as string,
        },
      })
    },
  })
  return {
    role,
    roleIsLoading,
  }
})
```

```vue{33} [role.vue]
<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('role.title')"
      :loading="rolesAreLoading"
    >
      <div class="flex flex-col gap-2">
        <div class="grid grid-cols-2 gap-4 2xl:grid-cols-2">
          <RoleCard
            v-for="role in roles"
            :key="role.id"
            :role="role"
            @click="() => toRole(role)"
          />
        </div>
      </div>
    </StructuralColumn>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n'

import type { RoleResponse } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { roles, rolesAreLoading } = useRoles()

const createModalOpen = ref(false)

const toRole = (role: RoleResponse) => {
  router.push(localePath(`/service/roles/${role.id}`))
}
</script>
```
:::

### Mutating State

When we want to update data, things are a bit different. We use pinia-colada to define a mutation for us that uses the
client sdk to post a role update to our api.

Now, here comes the magic: In this mutation, we invalidate query keys. As the roles have updated, we invalidate the
`roles` key. This triggers pinia-colada to automatiaclly refetch our `useRole` composable from before, giving us instant
state update.

However, we can even go one step forward: As an update in the rules might have the consequence that the logged-in user
might now have access to a new service, we **also** invalidate the suite key, triggering pinia-colada to re-fetch these
composables as well!

And the best part? We don't have to do anything, as the vue refs holdings these objects will change automatically and
vue will re-render the UI accordingly.

::: code-group
```ts [useUpdateRole.ts]
import { updateRole, type UpdateRoleRequest } from '@core/sdk/client'

export const useUpdateRole = defineMutation(() => {
  const queryCache = useQueryCache()

  const { mutateAsync: updateRoleMutation } = useMutation({
    mutation: async ({ roleId, updatedRole }: { roleId: string, updatedRole: UpdateRoleRequest }) => {
      await updateRole({
        composable: '$fetch',
        path: {
          role_id: roleId,
        },
        body: updatedRole,
      })
      queryCache.invalidateQueries({ key: ['roles'] })
      queryCache.invalidateQueries({ key: ['suite'] })
    },
  })
  return {
    updateRole: updateRoleMutation,
  }
})
```

```vue{28,31,35} [role.vue]
<template>
  <StructuralColumn
    :title="role?.name"
    close-route="/service/roles"
    :loading="roleIsLoading"
    size="small"
  >
    <div class="flex flex-col gap-12">
      <div class="flex flex-col gap-3">
        <h2 class="text-xl">
          {{ t('role.edit') }}
        </h2>
        <RoleEdit
          v-model="role"
        />
        <Button
          type="button"
          :label="t('role.save_button')"
          icon="pi pi-save"
          @click="saveRole"
        />
      </div>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
import { useUpdateRole } from '@core/composables/role/useUpdateRole'
import type { CreateRoleRequest, RoleResponse } from '@core/sdk/client'

const { updateRole } = useUpdateRole()
...

const saveRole = async () => {
  await updateRole({ roleId: role.value.id, updatedRole: clonedRole.value })
  toast.add({ severity: 'success', summary: t('role.role_saved.summary'), detail: t('role.role_saved.detail'), life: 3000 })
}
</script>
```
:::

**Key Features:**

- **Reactive Queries**: Automatic caching and invalidation
- **Loading States**: Built-in loading and error handling
- **Optimistic Updates**: Immediate UI updates with rollback on error
- **Background Refetching**: Automatic data synchronization

---

## The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging frontend components.

### Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

**Critical: Navigate to the aihub_web directory and install dependencies.** The frontend uses pnpm as the package
manager.

```bash
cd aihub_web/aihub_web
pnpm install
```

### Step 1: Development Server Setup

The frontend development server includes hot module replacement, API proxy, and live reloading.

```bash
# Start development server (port 8182)
pnpm dev
```

**Access Points:**

- **Frontend Application**: `http://localhost:3001`
- **API Proxy**: Automatically routes `/api/v1` to `http://localhost:8000`
- **Hot Reload**: Automatic reloading on file changes

### Step 2: Create Composables

If you have created a new API-Endpoint, re-generate the client sdk:

```bash
pnpm generate-sdk
```

Wrap your API endpoints in composables like documented above.

### Step 3: Create Page

Now, start with the service page. In the `pages` directory, each service has its dedicated page.

Usually, the root page like `/agents.vue` fetching all agents using a composable like `useAgents()`, where nested pages
like `/agents/agent-[agent_id]-[agent_class].vue` use a composable like `useAgent()` to fetch a specific instance of an
agent.

If an agent then has multiple sub-pages that show different information, like the agents threads, a visualization of its
workflow, etc. these are different pages as well.

```
pages
├── agents
│    ├── agent-[agent_id]-[agent_class]
│    │    ├── chat.vue
│    │    ├── overview.vue
│    │    ├── threads.vue
│    │    └── workflow.vue
│    └── agent-[agent_id]-[agent_class].vue
└── agents.vue
```

::: code-group
```vue [agents.vue]
<template>
  <StructuralScreen>
    <StructuralColumn
      :title="t('agent.title')"
      :loading="agentsAreLoading"
    >
      <div
        class="grid grid-cols-2 gap-4 2xl:grid-cols-2"
      >
        <AgentCard
          v-for="agent in agents"
          :key="agent.agent_id"
          :agent="agent"
          @click="() => toAgent(agent)"
        />
      </div>
    </StructuralColumn>

    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
import type { AgentDto } from '@core/sdk/client'

import { useLocalePath } from '#i18n'

const router = useRouter()
const localePath = useLocalePath()
const { t } = useI18n()

const { agents, agentsAreLoading } = useAgents()

const toAgent = (agent: AgentDto) => {
  router.push(localePath(`/service/agents/agent-${agent.agent_id}-${agent.agent_class}/overview`))
}
</script>
```

```vue [/agents/agent-[agent_id]-[agent_class].vue]
<template>
  <div class="flex flex-col gap-2">
    <SelectButton
      v-if="navItems"
      :model-value="activeNavItem"
      :options="navItems"
      data-key="key"
      option-label="name"
      size="small"
      @update:model-value="toNavItem"
    />
    <NuxtPage />
  </div>
</template>

<script setup lang="ts">
import type { NavItem } from '@core/types/NavItem'

const router = useRouter()
const route = useRoute()
const localePath = useLocalePath()
const { t } = useI18n()

const { agent } = useAgent()

const subPath = (path: string) => {
  return `/service/agents/agent-${route.params.agent_id}-${route.params.agent_class}/${path}`
}

const isActive = (path: string) => {
  return () => {
    const localizedPath = localePath(subPath(path))
    return route.path.startsWith(localizedPath)
  }
}

const navItems = computed<NavItem[]>(() => {
  const items: NavItem[] = [
    { name: t('agent.navigation.basic'), key: 'basic', path: subPath('overview'), isActive: isActive('overview') },
    { name: t('agent.navigation.workflow'), key: 'workflow', path: subPath('workflow'), isActive: isActive('workflow') },
    { name: t('agent.navigation.threads'), key: 'threads', path: subPath('threads'), isActive: isActive('threads') },
  ]
  if (agent.value?.is_conversational) {
    items.push({ name: t('agent.navigation.chat'), key: 'chat', path: subPath('chat'), isActive: isActive('chat') },
    )
  }
  return items
})

const toNavItem = (navItem: NavItem) => {
  router.push(localePath(navItem.path))
}

const activeNavItem = computed<NavItem | undefined>(() => {
  return navItems.value?.filter(navItem => navItem.isActive())[0]
})
</script>
```

```vue [/agents/agent-[agent_id]-[agent_class]/overview.vue]
<template>
  <StructuralColumn
    :title="agent?.agent_config.name"
    close-route="/service/agents"
    :loading="agentIsLoading"
    size="large"
  >
    <div class="flex flex-col gap-12">
      <span class="mb-4 block text-sm text-surface-500 dark:text-surface-400">
        {{ agent.agent_config.description }}
      </span>
      <Panel
        class="panel pt-5"
      >
        ...
      </Panel>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { agent, agentIsLoading } = useAgent()
</script>
```
:::

There are a few interesting things to note here. First, all pages fetch their own data, hence, they are all completely
independent of each other, simply re-using composables like `useAgent` as we let pinia-colada handle caching for us.

Second, you see multiple uses of `StructuralColumn` - that is simply a component that dominates our design system. It
intelligently waits to display any content before the data has finished loading, giving you the security that you can
freely use data like `agent` within the template without having to wait until it is loaded.

Third, you may have noticed that `/agents/agent-[agent_id]-[agent_class].vue` does not do anything - it is just a
`router`, giving the user the option to click on either *overview*, *workflow*, *threads* or *chat*. That is a common
pattern as well.

### Step 4: Create Components

::: info Component Creation
Now that you have the page, start extracting fitting sections as re-usable components.
:::

::: tip Do's
- **Do** check our components to see whather we have a component that already fulfils your needs
- **Do** re-use components or make them more flexible with additional props if you need to
- **Do** copy-paste components if you need something that is similar by design, but is a completely different domain /
  service
- **Do** check the primevue page regularly and find components that fit your needs
- **Do** find inspiration in their component library or their [PrimeBlocks](https://primeblocks.org/) website
:::

::: warning Don'ts
- **Don't** build low-level components like buttons. Instead, use the ones offered by PrimeVue.
- **Don't** write inline css, use tailwind
- **Don't** like custom css classes, use tailwind
- **Don't** overabstract components - we don't want to build a super complex data table ourselves. If we have one table
  for service X and a duplicate for service Y, that's fine.
:::

### Step 5: Add Internationalization

All user components must be translated into at least **German**, **English**, *French*\* and **Italian**. We have
dedicated locale yaml files for these languages.

::: code-group
```vue [myComponent.vue]
<template>
  <h1>{{ t('myFeature.title') }}</h1>
  <p>{{ t('myFeature.description') }}</p>
  <button>{{ t('myFeature.actions.create') }}</button>
</template>
<script setup lang="ts">
const { t } = useI18n()
</script>
```

```yaml [en.yaml]
myFeature:
  title: "My Feature"
  description: "Feature description"
  actions:
    create: "Create"
```

```yaml [de.yaml]
myFeature:
  title: "Mein Feature"
  description: "Feature-Beschreibung"
  actions:
    create: "Erstellen"
```
:::

We usually structure the i18n files by service as well.

### Step 6: Ensure Code Quality

Before committing your changes, use the provided npm scripts:

```bash
pnpm lint
```

**Code Quality Standards:**

- **ESLint**: Enforces code style and catches errors
- **TypeScript**: Strict typing with comprehensive type checking
- **Import Sorting**: Automatic import organization
- **Tailwind CSS**: Utility-first styling with consistent design system

---

## Glossary of Web Frontend Terms

This glossary defines terms, concepts, and technologies that have specific meaning within the `aihub_web` scope,
building upon the core AI-Hub terminology.

| Term                         | Definition                                                                                                                                                                |
| :--------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Composable**               | Vue 3 composition functions that encapsulate and reuse stateful logic. In aihub_web, composables manage API calls, state, and business logic using Pinia-Colada patterns. |
| **Pinia-Colada**             | Advanced state management library that provides reactive queries, mutations, and caching for Vue applications. Used extensively for API state management in aihub_web.    |
| **PrimeVue**                 | Comprehensive UI component library providing rich, accessible components. Forms the foundation of aihub_web's user interface with custom theming.                         |
| **Nuxt Layer**               | Nuxt 3 architectural pattern that allows sharing configuration, components, and composables. aihub_web is structured as a reusable layer.                                 |
| **SPA Mode**                 | Single Page Application mode where the entire app runs client-side with no server-side rendering. Enables rich interactivity and real-time updates.                       |
| **API Proxy**                | Development-time proxy configuration that routes API calls from the frontend to the backend service, enabling seamless local development.                                 |
| **Socket.io Integration**    | Real-time bidirectional communication system that enables live updates for chat, agent events, and system notifications.                                                  |
| **Vue Flow**                 | Workflow visualization library used for displaying agent workflows and process diagrams with interactive node-based interfaces.                                           |
| **ApexCharts**               | Charting library integration for displaying analytics, cost tracking, and performance metrics in dashboard components.                                                    |
| **File-based Routing**       | Nuxt 3 feature that automatically generates routes based on the file structure in the `pages/` directory.                                                                 |
| **Auto-imports**             | Nuxt 3 feature that automatically imports composables, components, and utilities without explicit import statements.                                                      |
| **Middleware**               | Functions that run before rendering pages, used for authentication, authorization, and route protection.                                                                  |
| **Locale Handler**           | Internationalization system supporting English, German, French, and Italian with automatic locale detection and switching.                                                |
| **Generated SDK**            | TypeScript client automatically generated from the API's OpenAPI specification, providing type-safe API interactions.                                                     |
| **Theme System**             | Custom PrimeVue theme configuration that provides consistent styling and dark mode support across the application.                                                        |
| **Event Display Components** | Specialized components for rendering different types of AI-Hub events (LLM events, chunk events, exception events) with rich formatting.                                  |
| **Thread Management**        | User interface for managing conversation threads between users and AI agents, including chat history and participant management.                                          |
| **Agent Dashboard**          | Administrative interface for monitoring agent performance, managing configurations, and viewing agent-specific analytics.                                                 |
| **Process Visualization**    | Interactive workflow diagrams that show the flow of agentic processes with real-time status updates.                                                                      |
| **Evaluation Interface**     | User interface for managing datasets, experiments, and AI model evaluations with results visualization.                                                                   |
| **Cost Tracking**            | Dashboard components for monitoring and analyzing AI model usage costs with detailed breakdowns and trends.                                                               |
