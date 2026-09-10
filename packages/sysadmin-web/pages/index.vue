<template>
  <div />
</template>

<script setup lang="ts">
// Overrides the inherited @swiss-ai-hub/web `pages/index.vue`, whose onMounted
// drives the regular tenant / select-tenant / OpenWebUI flow. sysadmin-web's
// home is the tenant-administration list; the global `sysadmin` middleware
// redirects `/{locale}` → `/{locale}/tenants`. This page just has to exist so
// the heavy inherited index page never runs here.
definePageMeta({ layout: 'sysadmin' })
</script>
