<template>
  <div>
    <h1>Thread {{ thread_id }}</h1>
    <h2>{{ $t('test') }}</h2>
    <ThreadChat :thread-id="thread_id" />
  </div>
</template>

<script lang="ts" setup>
const route = useRoute()

const thread_id = computed(() => route.params.id)
</script>

<style scoped>

</style>
