<template>
  <div>
    <h1>Home</h1>
    <p>
      {{ health }}
    </p>
  </div>
</template>

<script setup lang="ts">

import {getUser} from "@core/sdk/client";
const health = ref("");

getUser({
  composable: '$fetch',
})
  .then((user) => {
    console.log("health", user.name)
    health.value = user.name;
  })

</script>

<style scoped>


</style>
