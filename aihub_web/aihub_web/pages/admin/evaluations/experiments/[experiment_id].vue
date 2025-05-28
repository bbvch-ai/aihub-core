<template>
  <StructuralColumn
    :title="experiment?.name"
    close-route="/admin/evaluations/experiments"
    :loading="experimentIsLoading"
    size="large"
  >
    <EvaluationExperimentResults :experiment="experiment" />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { experiment, experimentIsLoading } = useExperiment()
</script>
