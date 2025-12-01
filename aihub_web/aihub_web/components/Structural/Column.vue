<template>
  <div class="relative flex w-full flex-col gap-3">
    <div
      :class="[
        'w-full max-w-full overflow-hidden rounded-3xl bg-white dark:bg-surface-900',
        sizeClass,
      ]"
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

const sizeClass = computed<string>(() => {
  return {
    small: '2xl:w-[680px]',
    normal: '2xl:w-[920px]',
    large: '2xl:w-[1440px]',
  }[props.size]
})

const router = useRouter()
const localePath = useLocalePath()
const close = () => {
  router.push(localePath(props.closeRoute))
}
</script>
