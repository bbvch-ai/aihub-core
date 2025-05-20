<template>
  <div class="relative flex grow flex-col gap-3">
    <div
      class="overflow-hidden rounded-3xl bg-white dark:bg-surface-900"
      :style="{ minWidth }"
    >
      <ProgressBar
        v-if="loading"
        mode="indeterminate"
        style="height: 2px"
      />
      <div
        v-else
        class="h-[2px] w-full"
      />
      <div
        v-if="loading === undefined || loading === false"
        class="p-8"
      >
        <div class="flex items-center justify-between">
          <h2 class="text-3xl">
            {{ title }}
          </h2>
          <i
            v-if="closeRoute"
            class="pi pi-times cursor-pointer text-xl"
            @click="close"
          />
        </div>
        <Divider />
        <slot />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  title: string
  closeRoute?: string
  size?: 'small' | 'normal' | 'large'
  loading?: boolean
}>(), {
  size: 'normal',
  loading: false,
})

const minWidth = computed<string>(() => {
  return {
    small: 680,
    normal: 920,
    large: 1440,
  }[props.size] + 'px'
})

const router = useRouter()
const localePath = useLocalePath()
const close = () => {
  router.push(localePath(props.closeRoute))
}
</script>
