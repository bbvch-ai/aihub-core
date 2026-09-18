<template>
  <Button
    v-if="props.labelled"
    class="w-full"
    :label="t('support.report_bug')"
    variant="text"
    icon="pi pi-exclamation-circle"
    icon-pos="right"
    @click="open"
  />
  <Button
    v-else
    v-tooltip="{ value: t('support.report_bug'), showDelay: 0 }"
    :aria-label="t('support.report_bug')"
    icon="pi pi-exclamation-circle"
    variant="text"
    size="large"
    @click="open"
  />
</template>

<script setup lang="ts">
const props = withDefaults(defineProps<{
  // Icon-only in the app rail, labelled inside the settings popover.
  labelled?: boolean
}>(), {
  labelled: false,
})

const { t } = useI18n()
const { open } = useIncidentReport()
</script>
