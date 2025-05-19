<template>
  <div class="content overflow-x-auto">
    <MDC
      :value="md"
      tag="article"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{
  md: string
}>()
</script>

<style scoped>
.content {
  @apply font-light text-xs
}
.content :deep(h1) {
  @apply mb-4 text-xl font-bold before:content-['#'] before:pr-1 before:text-gray-400;
}

.content :deep(h2) {
  @apply mt-6 text-lg font-bold before:content-['##'] before:pr-1 before:text-gray-400;
}

.content :deep(h3) {
  @apply mt-4 text-base font-bold before:content-['###'] before:pr-1 before:text-gray-400;;
}

.content :deep(h4) {
  @apply mt-4 font-bold before:content-['####'] before:pr-1 before:text-gray-400;;
}

.content :deep(p) {
  @apply mt-2 ;
}

.content :deep(blockquote) {
  @apply px-4 py-3 my-4 italic border-s-4 dark:border-gray-500/20 dark:bg-gray-800/20;
}

.content :deep(ul) {
  @apply list-disc list-outside mt-2;
}

.content :deep(ol) {
  @apply list-decimal list-outside mt-2;
}

.content :deep(ul > li) {
  @apply ml-4 mt-2;
}

.content :deep(ol > li) {
  @apply ml-6 mt-2;
}

.content :deep(strong) {
  @apply font-bold;
}

.content :deep(p a) {
  @apply text-white border-b border-dotted border-white after:content-['↗'] after:pl-[1px];
}
.content :deep(ul a) {
  @apply text-white border-b border-dotted border-white after:content-['↗'] after:pl-[1px];
}
.content :deep(table) {
  @apply my-8;
}
.content :deep(th) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left font-bold bg-surface-100 dark:bg-surface-800;
}
.content :deep(td) {
  @apply border border-surface-200 dark:border-surface-500 p-2 text-left;
}
</style>
