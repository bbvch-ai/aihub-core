<template>
  <div>
    <img
      :src="imageUrl"
      :alt="alt"
      :width="width"
      :height="height"
    >
    <p
      v-if="alt"
      class="text-[10px] italic leading-3 text-surface-500"
    >
      {{ alt }}
    </p>
  </div>
</template>

<script setup lang="ts">
import { getFileUrl } from '@core/sdk/client'

const props = defineProps<{
  src: string
  alt?: string
  width?: string | number
  height?: string | number
}>()

const { tenantId } = useTenant()
const imageUrl = ref<string | null>(props.src)

const fetchAndSetImageUrl = async () => {
  if (props.src.startsWith('http')) {
    return props.src
  }
  if (!tenantId.value) return

  let src = props.src
  if (src.includes('://')) {
    src = src.split('://')[1]
  }
  const parts = src.split('/')
  const [container, file_path] = [parts[0], parts.slice(1).join('/')]

  const { url } = await getFileUrl({
    composable: '$fetch',
    path: {
      tenant_id: tenantId.value!,
      container,
      file_path,
    },
  })
  imageUrl.value = url
}

onMounted(() => {
  fetchAndSetImageUrl()
})
</script>
