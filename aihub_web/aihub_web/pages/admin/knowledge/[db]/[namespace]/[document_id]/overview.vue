<template>
  <StructuralColumn
    :title="document?.document_title"
    :close-route="`/admin/knowledge/${route.params.db}/${route.params.namespace}`"
    :loading="documentIsLoading"
  >
    <div class="mt-16 rounded-3xl border border-surface-100 p-9 shadow-lg dark:border-surface-800">
      <KnowledgeDocumentOverview :document="document">
        <MarkdownRenderer
          :md="document.content"
        />
      </KnowledgeDocumentOverview>
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { document, documentIsLoading } = useDocument()
const route = useRoute()
</script>

<style scoped>

</style>
