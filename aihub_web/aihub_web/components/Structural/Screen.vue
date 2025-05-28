<template>
  <div class="flex h-[calc(100vh-50px)] w-full flex-col justify-start gap-2 overflow-auto bg-surface-50 dark:bg-surface-950">
    <div class="px-8 pt-8">
      <slot name="top" />
    </div>
    <div class="flex justify-start gap-8 px-8">
      <slot />
    </div>
  </div>
</template>
