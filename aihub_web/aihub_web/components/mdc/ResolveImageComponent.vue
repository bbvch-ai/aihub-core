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

const imageUrl = ref<string | null>(props.src)

const fetchAndSetImageUrl = async () => {
  if (props.src.startsWith('http')) {
    return props.src
  }

  console.log(props.src)
  const [container, file_path] = [props.src.split('/')[0], props.src.split('/').slice(1).join('/')]

  console.log({ container, file_path })

  const { url } = await getFileUrl({
    composable: '$fetch',
    path: {
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

<style scoped>

</style>
