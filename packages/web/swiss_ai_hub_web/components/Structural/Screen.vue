<template>
  <div class="flex h-[calc(100vh-50px)] w-full flex-col justify-start gap-2 overflow-auto bg-surface-50 dark:bg-surface-950">
    <div class="px-8 pt-8">
      <slot name="top" />
    </div>
    <div class="flex flex-col justify-start gap-8 px-8 2xl:flex-row">
      <slot />
    </div>
  </div>
</template>
