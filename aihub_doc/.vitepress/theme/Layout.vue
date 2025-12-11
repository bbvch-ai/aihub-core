<script setup>
import DefaultTheme from "vitepress/theme";
import { onMounted, nextTick } from "vue";
import { useRouter } from "vitepress";
import mediumZoom from "medium-zoom";
import GradientBackground from '../components/GradientBackground.vue'

const { Layout } = DefaultTheme;
const router = useRouter();

const setupMediumZoom = () => {
  nextTick(() => {
    mediumZoom("[data-zoomable]", {
      background: "transparent",
    });
  });
};

onMounted(setupMediumZoom);
router.onAfterRouteChange = setupMediumZoom;
</script>

<template>
  <Layout>
    <template #sidebar-nav-before>
      <GradientBackground />
    </template>
    <template #home-hero-before>
      <div class="home-gradient-wrapper">
        <GradientBackground />
      </div>
    </template>
  </Layout>
</template>

<style>
img.medium-zoom-image {
  transition: filter 0.3s ease;
}

html:not(.dark) img.medium-zoom-image {
  filter: invert(1);
}
.medium-zoom-overlay {
  backdrop-filter: blur(5rem);
}

.medium-zoom-overlay,
.medium-zoom-image--opened {
  z-index: 9999;
}
</style>