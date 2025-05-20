<template>
  <table class="w-full table-auto text-left">
    <thead>
      <tr>
        <th />
        <th>{{ t('costs.table.count') }}</th>
        <th>{{ t('costs.table.cost') }}</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td class="font-bold">
          {{ t('costs.table.input') }}
        </td>
        <td>{{ promptTokenCount }} </td>
        <td>{{ promptTokensCosts }} {{ t('costs.table.currency') }}</td>
      </tr>
      <tr>
        <td class="font-bold">
          {{ t('costs.table.output') }}
        </td>
        <td>{{ completionTokenCount }}</td>
        <td>{{ completionTokensCosts }} {{ t('costs.table.currency') }}</td>
      </tr>
      <tr v-if="embeddingTokenCount">
        <td class="font-bold">
          {{ t('costs.table.embedding') }}
        </td>
        <td>{{ embeddingTokenCount }}</td>
        <td>{{ embeddingTokensCosts }} {{ t('costs.table.currency') }}</td>
      </tr>
      <tr
        class="font-bold"
      >
        <td>
          {{ t('costs.table.total') }}
        </td>
        <td>{{ promptTokenCount + completionTokenCount + embeddingTokenCount }}</td>
        <td>{{ promptTokensCosts + completionTokensCosts + embeddingTokensCosts }} {{ t('costs.table.currency') }}</td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
defineProps<{
  promptTokenCount: number
  promptTokensCosts: number
  completionTokenCount: number
  completionTokensCosts: number
  embeddingTokenCount: number
  embeddingTokensCosts: number
}>()

const { t } = useI18n()
</script>
