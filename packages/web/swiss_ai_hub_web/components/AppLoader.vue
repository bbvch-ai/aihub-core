<template>
  <div
    class="loader"
    :style="{ '--loader-size': `${size}px`, '--loader-step': `${stepPx}px` }"
  />
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    size?: number
  }>(),
  {
    size: 64,
  },
)

// Round to integer pixels to avoid sub-pixel rendering artifacts in the animation
const stepPx = computed(() => Math.round(props.size * 0.547))
</script>

<style scoped>
.loader {
  position: relative;
  width: var(--loader-size);
  height: var(--loader-size);
  overflow: hidden;
}

.loader:before,
.loader:after {
  content: "";
  position: absolute;
  border-radius: 50px;
  box-shadow: 0 0 0 3px inset #808080;
  animation: loader-spin 2.5s infinite;
  will-change: inset;
}

.loader:after {
  animation-delay: -1.25s;
}

@keyframes loader-spin {
  0%    { inset: 0 var(--loader-step) var(--loader-step) 0; }
  12.5% { inset: 0 var(--loader-step) 0 0; }
  25%   { inset: var(--loader-step) var(--loader-step) 0 0; }
  37.5% { inset: var(--loader-step) 0 0 0; }
  50%   { inset: var(--loader-step) 0 0 var(--loader-step); }
  62.5% { inset: 0 0 0 var(--loader-step); }
  75%   { inset: 0 0 var(--loader-step) var(--loader-step); }
  87.5% { inset: 0 0 var(--loader-step) 0; }
  100%  { inset: 0 var(--loader-step) var(--loader-step) 0; }
}
</style>
