<template>
  <div
    ref="filesPanelRef"
    class="relative h-[calc(100vh-50px)] w-1/2 min-w-[800px] overflow-y-auto border-l border-surface-200 p-6 dark:border-surface-700"
  >
    <div class="mb-4">
      <h2 class="text-2xl font-semibold">
        {{ t('userFiles.title') }}
      </h2>
    </div>

    <UserFilesBrowser
      :initial-folder="`conversations/${threadId}`"
      stacked
    />

    <div
      class="fixed top-1/2 -translate-y-1/2"
      :style="{ left: `${panelLeftPosition - 16}px` }"
    >
      <i
        class="pi pi-chevron-right cursor-pointer rounded-full border border-surface-200 bg-surface-0 p-3 hover:bg-surface-100 dark:border-surface-700 dark:bg-surface-900 hover:dark:bg-surface-800"
        @click="closeFiles"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const router = useRouter()
const tenantPath = useTenantPath()
const { t } = useI18n()

const threadId = computed(() => route.params.thread_id as string)
const filesPanelRef = ref(null)
const panelBounding = useElementBounding(filesPanelRef)
const panelLeftPosition = computed(() => panelBounding.left.value)

const closeFiles = () => {
  router.push(tenantPath('/service/openai'))
}
</script>
