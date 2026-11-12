<template>
  <StructuralScreen>
    <NuxtPage />
  </StructuralScreen>
</template>

<script setup lang="ts">
const props = defineProps<{
  memoryType: 'user' | 'organization'
}>()

const router = useRouter()
const route = useRoute()
const tenantPath = useTenantPath()

const basePath = computed(() => `/service/${props.memoryType}-memories`)

onMounted(() => {
  if (route.path === tenantPath(basePath.value)) {
    router.push({
      path: tenantPath(`${basePath.value}/list`),
      query: route.query,
    })
  }
})
</script>
