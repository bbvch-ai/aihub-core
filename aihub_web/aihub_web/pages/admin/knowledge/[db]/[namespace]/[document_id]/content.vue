<template>
  <StructuralColumn
    :title="document?.title ?? ''"
    close-route="/admin/knowledge"
    :loading="documentIsLoading"
  >
    <div class="mt-16 rounded-3xl border border-surface-100 p-9 shadow-lg dark:border-surface-800">
      <MarkdownRenderer
        :md="document.text"
      />
    </div>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { document, documentIsLoading } = useDocument()
</script>
