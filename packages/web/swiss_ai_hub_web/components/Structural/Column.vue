<template>
  <div class="relative flex flex-col gap-3 max-2xl:w-full">
    <div
      :class="[
        'overflow-hidden rounded-3xl bg-white dark:bg-surface-900 max-2xl:w-full max-2xl:max-w-full',
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
        class="p-6"
      >
        <div class="flex items-center justify-between font-bold">
          <h2
            v-if="!childColumn"
            class="text-2xl"
          >
            {{ title }}
          </h2>
          <h3
            v-else
            class="text-xl"
          >
            {{ title }}
          </h3>
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
  childColumn?: boolean
}>(), {
  size: 'normal',
  loading: false,
  childColumn: false,
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
