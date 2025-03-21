<template>
  <Handle
    type="target"
    :position="Position.Left"
  />
  <div class="bg-red-500 text-white rounded-md shadow-md border border-gray-100 overflow-hidden p-6 text-lg font-bold">
    {{ props.id }}
  </div>
  <Handle
    type="source"
    :position="Position.Right"
  />
</template>

<script setup>
import { Handle, Position } from '@vue-flow/core'

const props = defineProps({
  id: {
    type: String,
    required: true,
  },
  data: {
    type: Object,
    required: true,
  },
})
</script>

<script>
export default {
  inheritAttrs: false,
}
</script>
