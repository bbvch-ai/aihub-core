<template>
  <StructuralColumn
    :title="t('thread.events.title')"
    :close-route="`/service/processes/${route.params.process_class}-${route.params.process_id}/walkthroughs`"
    :loading="false"
  >
    <p>This is overview</p>
  </StructuralColumn>
</template>

<script setup lang="ts">
const route = useRoute()
const { t } = useI18n()
</script>
