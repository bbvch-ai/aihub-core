<template>
  <div class="vt-box-container next-steps">
    <a 
      v-for="item in items" 
      :key="item.title"
      class="vt-box" 
      :href="item.href"
    >
      <p class="next-steps-link">{{ item.title }}</p>
      <p class="next-steps-caption">{{ item.description }}</p>
    </a>
  </div>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    required: true,
    validator: (items) => {
      return items.every(item => 
        item.title && 
        item.description && 
        item.href
      )
    }
  }
})
</script>

<style scoped>
.vt-box-container {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin: 2rem 0;
}

.vt-box {
  display: block;
  padding: 1.5rem;
  border: 1px solid var(--vp-c-border);
  border-radius: 8px;
  text-decoration: none !important;
  color: var(--vp-c-text-1);
  transition: all 0.25s ease;
  cursor: pointer;
}

.vt-box:hover {
  border-color: var(--vp-c-brand-2);
  transform: translateY(-2px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}

.dark .vt-box:hover {
  box-shadow: 0 4px 16px rgba(255, 255, 255, 0.05);
}

.next-steps-link {
  margin: 0 0 0.5rem 0;
  font-size: 1.125rem;
  font-weight: 700;
  color: var(--vp-c-text-1);
  text-align: center;
}

.next-steps-caption {
  margin: 0;
  font-size: 0.875rem;
  font-weight: 300;
  color: var(--vp-c-text-2);
  line-height: 1.5;
  text-align: center;
  text-decoration: none;
}

.vt-box:hover .next-steps-caption {
  text-decoration: none;
}

@media (max-width: 768px) {
  .vt-box-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
}
</style>