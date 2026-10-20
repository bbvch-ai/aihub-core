<template>
  <StructuralColumn
    :title="document?.document_title"
    :close-route="`/service/knowledge/${route.params.db}/${route.params.namespace}`"
    :loading="documentIsLoading"
  >
    <div class="mt-16 rounded-3xl border border-surface-100 p-9 shadow-lg dark:border-surface-800">
      <KnowledgeDocumentOverview :document="document">
        <MarkdownRenderer
          :md="md"
        />
      </KnowledgeDocumentOverview>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { document, documentIsLoading } = useDocument()
const route = useRoute()

const md = computed<string>(() => {
  if (documentIsLoading.value) {
    return ''
  }

  const content = document.value?.content
  if (!content) {
    return ''
  }

  return toMdcMarkdown(content)
})
</script>
