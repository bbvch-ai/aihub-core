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

  return content
    // Replace our custom <figure>-tags surrounding our images
    .replace(/(?:<|&lt;)figure(?:>|&gt;)/g, '::MarkdownFigure\n')
    .replace(/(?:<|&lt;)\/figure(?:>|&gt;)/g, '\n::')

    // Replace our custom <table>-tag surrounding our tables
    .replace(/(?:<|&lt;)table(?:>|&gt;)/g, '::MarkdownTable\n')
    .replace(/(?:<|&lt;)\/table(?:>|&gt;)/g, '\n::')
})
</script>
