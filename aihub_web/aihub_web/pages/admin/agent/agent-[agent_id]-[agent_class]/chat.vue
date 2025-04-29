<template>
  <div class="relative flex flex-col gap-2">
    <p class="text-xl font-bold">
      Chat
    </p>
    <div>
      <div />
      <div>
        <Textarea
          v-model="userInput"
          class="w-full"
          auto-resize
          rows="5"
          cols="30"
        />
        <Button
          label="Submit"
          class="w-full"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
const userInput = ref<string>('')
</script>

<style scoped>

</style>
