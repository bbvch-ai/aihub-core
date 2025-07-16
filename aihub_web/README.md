# AI-Hub Web Frontend Developer's Guide

## 1. Foundational Knowledge of Web Frontend Development

This section covers the foundational architecture, patterns, and terminology you need to know before building frontend components.

### Introduction to `aihub_web`

You are contributing to the **aihub_web** scope, which contains the main web frontend application within the AI-Hub platform. This scope implements the user interface that connects users to AI agents, processes, and system management capabilities through an intuitive, modern web application built with Nuxt 3.

### Project Structure

The `aihub_web` scope is organized as follows:

```
aihub_web/
├── aihub_web/                  # Main application source
│   ├── components/             # Vue components organized by domain
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
├── package.json                # Dependencies and scripts
├── nuxt.config.ts             # Nuxt configuration
├── tailwind.config.mjs        # Tailwind CSS configuration
└── eslint.config.js           # ESLint configuration
```

### Glossary of Web Frontend Terms

This glossary defines terms, concepts, and technologies that have specific meaning within the `aihub_web` scope, building upon the core AI-Hub terminology.

| Term | Definition |
| :--- | :--- |
| **Composable** | Vue 3 composition functions that encapsulate and reuse stateful logic. In aihub_web, composables manage API calls, state, and business logic using Pinia-Colada patterns. |
| **Pinia-Colada** | Advanced state management library that provides reactive queries, mutations, and caching for Vue applications. Used extensively for API state management in aihub_web. |
| **PrimeVue** | Comprehensive UI component library providing rich, accessible components. Forms the foundation of aihub_web's user interface with custom theming. |
| **Nuxt Layer** | Nuxt 3 architectural pattern that allows sharing configuration, components, and composables. aihub_web is structured as a reusable layer. |
| **SPA Mode** | Single Page Application mode where the entire app runs client-side with no server-side rendering. Enables rich interactivity and real-time updates. |
| **API Proxy** | Development-time proxy configuration that routes API calls from the frontend to the backend service, enabling seamless local development. |
| **Socket.io Integration** | Real-time bidirectional communication system that enables live updates for chat, agent events, and system notifications. |
| **Vue Flow** | Workflow visualization library used for displaying agent workflows and process diagrams with interactive node-based interfaces. |
| **ApexCharts** | Charting library integration for displaying analytics, cost tracking, and performance metrics in dashboard components. |
| **File-based Routing** | Nuxt 3 feature that automatically generates routes based on the file structure in the `pages/` directory. |
| **Auto-imports** | Nuxt 3 feature that automatically imports composables, components, and utilities without explicit import statements. |
| **Middleware** | Functions that run before rendering pages, used for authentication, authorization, and route protection. |
| **Locale Handler** | Internationalization system supporting English, German, French, and Italian with automatic locale detection and switching. |
| **Generated SDK** | TypeScript client automatically generated from the API's OpenAPI specification, providing type-safe API interactions. |
| **Theme System** | Custom PrimeVue theme configuration that provides consistent styling and dark mode support across the application. |
| **Event Display Components** | Specialized components for rendering different types of AI-Hub events (LLM events, chunk events, exception events) with rich formatting. |
| **Thread Management** | User interface for managing conversation threads between users and AI agents, including chat history and participant management. |
| **Agent Dashboard** | Administrative interface for monitoring agent performance, managing configurations, and viewing agent-specific analytics. |
| **Process Visualization** | Interactive workflow diagrams that show the flow of agentic processes with real-time status updates. |
| **Evaluation Interface** | User interface for managing datasets, experiments, and AI model evaluations with results visualization. |
| **Cost Tracking** | Dashboard components for monitoring and analyzing AI model usage costs with detailed breakdowns and trends. |

### The Component Architecture

The frontend follows a component-based architecture with clear separation of concerns:

```vue
<!-- Domain-specific components organized by feature -->
<template>
  <div class="agent-card">
    <AgentAvatar :agent="agent" />
    <AgentInfo :agent="agent" />
    <AgentActions :agent="agent" @start="startAgent" />
  </div>
</template>

<script setup lang="ts">
// TypeScript everywhere with strict typing
interface Props {
  agent: AgentDto
}

const props = defineProps<Props>()
const { startAgent } = useAgent()
</script>
```

**Key Principles:**
- **Domain-Driven Organization**: Components grouped by business domain (Agent, Chat, Process, etc.)
- **Composition API**: Modern Vue 3 patterns with `<script setup>` syntax
- **TypeScript Integration**: Full type safety from API to components
- **Reactive State Management**: Pinia-Colada for efficient API state handling

### State Management with Pinia-Colada

The application uses Pinia-Colada for sophisticated state management:

```typescript
// Composables encapsulate API calls and state
export const useAgents = defineQuery(() => {
  const { data: agents, isPending: agentsAreLoading } = useQuery<AgentDto[]>({
    key: () => ['agents'],
    staleTime: minutesToMilliseconds(5),
    query: async () => {
      return await getAgents({ composable: '$fetch' })
    },
  })
  return { agents, agentsAreLoading }
})
```

**Key Features:**
- **Reactive Queries**: Automatic caching and invalidation
- **Loading States**: Built-in loading and error handling
- **Optimistic Updates**: Immediate UI updates with rollback on error
- **Background Refetching**: Automatic data synchronization

---

## 2. The Step-by-Step Development Workflow

This section provides a practical, step-by-step guide to building, testing, and debugging frontend components.

### Prerequisites: Infrastructure and Environment

Before you begin, ensure you have completed the infrastructure setup from the root project documentation.

```bash
# Start required services from the project root
docker compose -f docker-compose.yml -f milvus-standalone-docker-compose.yml -f docker-compose-webui.yml up -d
```

**Critical: Navigate to the aihub_web directory and install dependencies.** The frontend uses pnpm as the package manager.

```bash
cd aihub_web
pnpm install
```

### Step 1: Development Server Setup

The frontend development server includes hot module replacement, API proxy, and live reloading.

```bash
# Start development server (port 8182)
pnpm dev

# Alternative: with specific port
pnpm dev --port 3000
```

**Access Points:**
- **Frontend Application**: `http://localhost:8182`
- **API Proxy**: Automatically routes `/api/v1` to `http://localhost:8000`
- **Hot Reload**: Automatic reloading on file changes

### Step 2: Create Components and Composables

Follow this pattern for building new features:

1. **Create the Composable**: Define the data layer and business logic.
   ```typescript
   // composables/my-feature/useMyFeature.ts
   import { getMyFeatureData, type MyFeatureDto } from '@core/sdk/client'
   import { useQuery } from '@pinia/colada'
   
   export const useMyFeature = defineQuery(() => {
     const { data: features, isPending: isLoading } = useQuery<MyFeatureDto[]>({
       key: () => ['my-feature'],
       staleTime: minutesToMilliseconds(5),
       query: async () => {
         return await getMyFeatureData({ composable: '$fetch' })
       },
     })
   
     return { features, isLoading }
   })
   ```

2. **Create the Component**: Build the UI component.
   ```vue
   <!-- components/MyFeature/Card.vue -->
   <template>
     <Card class="my-feature-card">
       <template #header>
         <div class="flex items-center gap-2">
           <Icon name="my-feature" />
           <h3>{{ feature.name }}</h3>
         </div>
       </template>
       <template #content>
         <p>{{ feature.description }}</p>
         <MyFeatureActions :feature="feature" />
       </template>
     </Card>
   </template>
   
   <script setup lang="ts">
   import type { MyFeatureDto } from '@core/sdk/client'
   
   interface Props {
     feature: MyFeatureDto
   }
   
   const props = defineProps<Props>()
   </script>
   ```

3. **Create the Page**: Integrate components into a page.
   ```vue
   <!-- pages/service/my-feature.vue -->
   <template>
     <div class="my-feature-page">
       <h1>{{ t('myFeature.title') }}</h1>
       <div v-if="isLoading" class="loading">
         <ProgressSpinner />
       </div>
       <div v-else class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
         <MyFeatureCard
           v-for="feature in features"
           :key="feature.id"
           :feature="feature"
         />
       </div>
     </div>
   </template>
   
   <script setup lang="ts">
   const { t } = useI18n()
   const { features, isLoading } = useMyFeature()
   
   definePageMeta({
     middleware: 'auth',
     layout: 'default',
   })
   </script>
   ```

### Step 3: Add Internationalization

All user-facing text must support the four required languages:

```yaml
# i18n/locales/en.yaml
myFeature:
  title: "My Feature"
  description: "Feature description"
  actions:
    create: "Create"
    edit: "Edit"
    delete: "Delete"
  
# i18n/locales/de.yaml
myFeature:
  title: "Mein Feature"
  description: "Feature-Beschreibung"
  actions:
    create: "Erstellen"
    edit: "Bearbeiten"
    delete: "Löschen"
```

### Step 4: API Integration

The frontend uses a generated SDK that provides type-safe API interactions:

```typescript
// Generated SDK usage
import { 
  getMyFeatureData, 
  createMyFeature, 
  updateMyFeature,
  type MyFeatureDto,
  type CreateMyFeatureRequest 
} from '@core/sdk/client'

// Query example
const { data } = await getMyFeatureData({ composable: '$fetch' })

// Mutation example
const newFeature = await createMyFeature({
  composable: '$fetch',
  body: { name: 'New Feature', description: 'Description' }
})
```

**SDK Regeneration:**
```bash
# Regenerate SDK when API changes
pnpm generate-sdk
```

### Step 5: Testing and Debugging

#### Development Tools

- **Vue DevTools**: Browser extension for component inspection
- **Network Tab**: Monitor API calls and responses
- **Console Logging**: Use `console.log()` for debugging composables

#### Common Debugging Patterns

```typescript
// Debug composable state
export const useMyFeature = defineQuery(() => {
  const query = useQuery<MyFeatureDto[]>({
    key: () => ['my-feature'],
    query: async () => {
      console.log('Fetching my feature data...')
      const data = await getMyFeatureData({ composable: '$fetch' })
      console.log('Received data:', data)
      return data
    },
  })
  
  // Debug reactive state
  watchEffect(() => {
    console.log('Query state:', query.asyncStatus.value)
    console.log('Data:', query.data.value)
  })
  
  return query
})
```

### Step 6: Ensure Code Quality

Before committing your changes, use the provided npm scripts:

```bash
# Lint and fix code issues
pnpm lint

# Build for production
pnpm build
```

**Code Quality Standards:**
- **ESLint**: Enforces code style and catches errors
- **TypeScript**: Strict typing with comprehensive type checking
- **Import Sorting**: Automatic import organization
- **Tailwind CSS**: Utility-first styling with consistent design system

---

## 3. Frontend Design Patterns and Best Practices

This section covers established patterns and best practices for building robust frontend components.

### Component Organization Patterns

#### Domain-Driven Component Structure

Components are organized by business domain rather than technical concerns:

```
components/
├── Agent/              # Agent management components
│   ├── Avatar.vue      # Agent avatar display
│   ├── Card.vue        # Agent card layout
│   └── List.vue        # Agent list container
├── Chat/               # Chat interface components
│   ├── Message.vue     # Individual message component
│   ├── Thread.vue      # Thread display
│   └── SourceNodes.vue # Source citations
└── Process/            # Process management components
    ├── Form.vue        # Process configuration form
    └── Visualization.vue # Process workflow diagram
```

#### Reusable Component Patterns

```vue
<!-- Base component with slot patterns -->
<template>
  <Card class="base-card">
    <template #header>
      <slot name="header" />
    </template>
    <template #content>
      <slot />
    </template>
    <template #footer>
      <slot name="footer" />
    </template>
  </Card>
</template>

<!-- Composition with multiple components -->
<template>
  <AgentCard>
    <template #header>
      <AgentAvatar :agent="agent" />
      <AgentStatus :agent="agent" />
    </template>
    <AgentMetrics :agent="agent" />
    <template #footer>
      <AgentActions :agent="agent" />
    </template>
  </AgentCard>
</template>
```

### State Management Patterns

#### Query Patterns with Pinia-Colada

```typescript
// Basic query pattern
export const useBasicQuery = defineQuery(() => {
  return useQuery({
    key: () => ['basic-data'],
    query: async () => await fetchData(),
  })
})

// Parameterized query pattern
export const useParameterizedQuery = defineQuery((id: string) => {
  return useQuery({
    key: () => ['data', id],
    query: async () => await fetchDataById(id),
  })
})

// Paginated query pattern
export const usePaginatedQuery = defineQuery(() => {
  const currentPage = ref(1)
  const pageSize = ref(10)
  
  const query = useQuery({
    key: () => ['paginated-data', { page: currentPage.value, size: pageSize.value }],
    query: async () => await fetchPaginatedData({
      page: currentPage.value,
      size: pageSize.value,
    }),
    placeholderData: previousData => previousData,
  })
  
  return { ...query, currentPage, pageSize }
})
```

#### Mutation Patterns

```typescript
// Basic mutation pattern
export const useCreateMutation = () => {
  return useMutation({
    mutation: async (data: CreateRequest) => await createData(data),
    onSuccess: () => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['data'] })
    },
  })
}

// Optimistic update pattern
export const useOptimisticMutation = () => {
  return useMutation({
    mutation: async (data: UpdateRequest) => await updateData(data),
    onMutate: async (data) => {
      // Optimistically update the UI
      const previousData = queryClient.getQueryData(['data', data.id])
      queryClient.setQueryData(['data', data.id], { ...previousData, ...data })
      return { previousData }
    },
    onError: (error, variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['data', variables.id], context.previousData)
    },
  })
}
```

### Real-time Communication Patterns

#### Socket.io Integration

```typescript
// Socket connection composable
export const useSocket = () => {
  const socket = ref<Socket | null>(null)
  
  const connect = () => {
    socket.value = io('/api/v1', {
      auth: { token: await getToken() },
    })
    
    socket.value.on('connect', () => {
      console.log('Connected to socket')
    })
    
    socket.value.on('disconnect', () => {
      console.log('Disconnected from socket')
    })
  }
  
  const disconnect = () => {
    socket.value?.disconnect()
    socket.value = null
  }
  
  return { socket, connect, disconnect }
}

// Real-time event handling
export const useRealTimeEvents = (threadId: string) => {
  const { socket } = useSocket()
  const events = ref<Event[]>([])
  
  const subscribeToThread = () => {
    socket.value?.emit('join_thread', threadId)
    socket.value?.on('thread_event', (event: Event) => {
      events.value.push(event)
    })
  }
  
  const unsubscribeFromThread = () => {
    socket.value?.emit('leave_thread', threadId)
    socket.value?.off('thread_event')
  }
  
  return { events, subscribeToThread, unsubscribeFromThread }
}
```

### UI Component Patterns

#### Event Display Components

```vue
<!-- Dynamic event component rendering -->
<template>
  <div class="event-display">
    <component 
      :is="getEventComponent(event)"
      :event="event"
      :key="event.id"
    />
  </div>
</template>

<script setup lang="ts">
import type { Event } from '@core/sdk/client'

interface Props {
  event: Event
}

const props = defineProps<Props>()

// Dynamic component mapping
const getEventComponent = (event: Event) => {
  const eventType = event._parent_event_names?.[0]
  
  switch (eventType) {
    case 'ChunkEvent':
      return resolveComponent('EventDisplayChunkEvent')
    case 'LLMEvent':
      return resolveComponent('EventDisplayLLMEvent')
    case 'ExceptionEvent':
      return resolveComponent('EventDisplayExceptionEvent')
    default:
      return resolveComponent('EventDisplayUnknownEvent')
  }
}
</script>
```

