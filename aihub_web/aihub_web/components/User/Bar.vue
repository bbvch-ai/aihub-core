<template>
  <div class="flex flex-row items-center gap-5 pr-3">
    <Button
      :icon="isDark ? 'pi pi-sun' : 'pi pi-moon'"
      variant="text"
      rounded
      aria-label="Toggle Dark Mode"
      @click="toggleDarkMode()"
    />

    <NotificationNotifications/>
    <div
      v-if="myUserIsLoading"
      class="flex flex-row gap-2"
    >
      <div class="flex flex-col gap-1">
        <Skeleton
          width="6rem"
          height="1rem"
        />
        <Skeleton
          width="10rem"
          height="1rem"
        />
      </div>
      <Skeleton
        shape="circle"
        size="2.5rem"
        class="mr-2"
      />
    </div>
    <div
      v-else
      class="flex items-center gap-5 pr-5"
    >
      <div>
        <p class="text-xs font-bold">
          {{ myUser?.name }}
        </p>
        <p class="text-xs">
          {{ myUser?.email }}
        </p>
      </div>
      <Avatar
        :image="myUser?.profile_image ?? undefined"
        :label="!myUser?.profile_image ? userInitials : undefined"
        shape="circle"
        size="normal"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import {useDark} from '@vueuse/core';
import {computed} from 'vue';

const {myUser, myUserIsLoading} = useMyUser();

const userInitials = computed(() =>
  myUser.value?.name?.split(' ').map(n => n[0]).join(''),
);

// Initialize the dark mode reactive state with persistence
const isDark = useDark({storageKey: 'dark'});

function toggleDarkMode() {
  isDark.value = !isDark.value;
}
</script>
