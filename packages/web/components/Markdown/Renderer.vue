<template>
  <div class="content overflow-x-auto">
    <MDC
      :value="md"
      :tag="false"
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
  @apply my-8 text-xl font-bold before:content-['#'] before:pr-1 before:text-gray-400;
}

.content :deep(h2) {
  @apply mt-12 text-lg font-bold before:content-['##'] before:pr-1 before:text-gray-400;
}

.content :deep(h3) {
  @apply mt-10 text-base font-bold before:content-['###'] before:pr-1 before:text-gray-400;
}

.content :deep(h4) {
  @apply mt-8 font-bold before:content-['####'] before:pr-1 before:text-gray-400;
}

.content :deep(h5) {
  @apply mt-6 font-bold before:content-['#####'] before:pr-1 before:text-gray-400;
}

.content :deep(h6) {
  @apply mt-4 font-bold before:content-['######'] before:pr-1 before:text-gray-400;
}

.content :deep(p) {
  @apply mt-2 ;
}

.content :deep(blockquote) {
  @apply px-4 py-3 my-4 italic border-s-4 dark:border-gray-500/20 dark:bg-surface-800/20;
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
  @apply  border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
}
.content :deep(ul a) {
  @apply  border-b border-dotted border-gray-400  after:content-['↗'] after:pl-[1px];
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
