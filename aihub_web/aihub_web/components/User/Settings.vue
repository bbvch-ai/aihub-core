<template>
  <Button
    icon="pi pi-cog"
    aria-label="Settings"
    variant="text"
    size="large"
    @click="toggle"
  />
  <Popover
    ref="op"
  >
    <Button
      class="w-full"
      label="Logout"
      variant="text"
      icon="pi pi-arrow-circle-right"
      icon-pos="right"
      @click="auth.logout"
    />
  </Popover>
</template>

<script setup lang="ts">
const auth = useAuth()

const op = ref()
const toggle = (event: Event) => {
  op.value.toggle(event)
}
</script>

<style scoped>

</style>
