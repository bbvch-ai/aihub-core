<template>
  <StructuralColumn
    :title="experiment?.name"
    close-route="/admin/evaluation/experiment"
    :loading="experimentIsLoading"
    size="large"
  >
    <EvaluationExperimentResults :experiment="experiment" />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { experiment, experimentIsLoading } = useExperiment()
</script>
