<template>
  <table class="w-full table-auto text-left">
    <thead>
      <tr>
        <th />
        <th>Anzahl</th>
        <th>Kosten</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="font-bold">
          Input
        </td>
        <td>{{ promptTokenCount }} </td>
        <td>{{ promptTokensCosts }} CHF</td>
      </tr>
      <tr>
        <td class="font-bold">
          Output
        </td>
        <td>{{ completionTokenCount }}</td>
        <td>{{ completionTokensCosts }} CHF</td>
      </tr>
      <tr v-if="embeddingTokenCount">
        <td class="font-bold">
          Embedding
        </td>
        <td>{{ embeddingTokenCount }}</td>
        <td>{{ embeddingTokensCosts }} CHF</td>
      </tr>
      <tr
        class="font-bold"
      >
        <td>
          Total
        </td>
        <td>{{ promptTokenCount + completionTokenCount + embeddingTokenCount }}</td>
        <td>{{ promptTokensCosts + completionTokensCosts + embeddingTokensCosts }} CHF</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
const props = defineProps<{
  promptTokenCount: number
  promptTokensCosts: number
  completionTokenCount: number
  completionTokensCosts: number
  embeddingTokenCount: number
  embeddingTokensCosts: number
}>()
</script>

<style scoped>

</style>
