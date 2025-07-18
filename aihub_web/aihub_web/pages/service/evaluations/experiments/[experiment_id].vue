<template>
  <StructuralColumn
    :title="experiment?.name"
    close-route="/service/evaluations/experiments"
    :loading="experimentIsLoading"
    size="large"
  >
    <EvaluationExperimentResults :experiment="experiment" />
  </StructuralColumn>
</template>

<script setup lang="ts">
const { experiment, experimentIsLoading } = useExperiment()
</script>
