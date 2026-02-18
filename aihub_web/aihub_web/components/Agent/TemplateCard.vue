<template>
  <div
    class="flex cursor-pointer flex-col gap-3 rounded-xl border border-surface-200 p-4 hover:bg-surface-100 dark:border-surface-800 hover:dark:bg-surface-800"
    @click="emit('click')"
  >
    <div class="flex items-center gap-2">
      <div
        class="flex items-center justify-center rounded-full bg-white p-3 dark:bg-surface-900"
      >
        <Icon
          :name="templateIcon"
          size="1.5em"
        />
      </div>
      <div>
        <h3 class="font-semibold opacity-80">
          {{ templateName }}
        </h3>
        <p class="text-xs font-light opacity-70">
          {{ agentClassName }}
        </p>
      </div>
    </div>
    <div>
      <span class="text-xs">
        {{ templateDescription }}
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  template: Record<string, unknown>
  agentClassName: string
  locale: string
}>()

const emit = defineEmits<{
  click: []
}>()

const templateName = computed(() => {
  const name = props.template.name as Record<string, string> | undefined
  return name?.[props.locale] ?? name?.en ?? ''
})

const templateDescription = computed(() => {
  const desc = props.template.description as Record<string, string> | undefined
  return desc?.[props.locale] ?? desc?.en ?? ''
})

const templateIcon = computed(() => {
  return (props.template.icon as string) ?? 'meteor-icons:robot'
})
</script>
