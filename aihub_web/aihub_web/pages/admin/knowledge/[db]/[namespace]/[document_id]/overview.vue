<template>
  <StructuralColumn
    title="Events"
    close-route="/admin/knowledge"
    :loading="documentIsLoading"
  >
    <p>Document: {{ document?.title }}</p>
  </StructuralColumn>
</template>

<script setup lang="ts">
const { document, documentIsLoading } = useDocument()
</script>

<style scoped>

</style>
