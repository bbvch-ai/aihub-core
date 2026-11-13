<template>
  <component
    :is="tag"
    ref="element"
    v-tooltip.top="isTruncated ? text : undefined"
    class="truncate"
  >
    {{ text }}
  </component>
</template>

<script setup lang="ts">
withDefaults(defineProps<{
  text: string
  tag?: string
}>(), {
  tag: 'span',
})

const element = useTemplateRef<HTMLElement>('element')
const isTruncated = ref(false)

// Width changes and text changes (e.g. a locale switch) can both start or stop the truncation.
const measure = () => {
  isTruncated.value = !!element.value && element.value.scrollWidth > element.value.clientWidth
}
useResizeObserver(element, measure)
useMutationObserver(element, measure, { characterData: true, childList: true, subtree: true })
</script>
