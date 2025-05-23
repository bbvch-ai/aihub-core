<template>
  <div class="flex h-[calc(100vh-50px)] w-full justify-start flex-col gap-2 overflow-auto bg-surface-50 dark:bg-surface-950">
    <div class="px-8 pt-8">
      <slot name="top" />
    </div>
    <div class="flex gap-8 px-8 justify-start">
      <slot />
    </div>
  </div>
</template>
