<template>
  <Toaster />
  <router-view v-slot="{ Component }">
    <transition name="fade">
      <component :is="Component" />
    </transition>
  </router-view>
</template>

<script setup lang="ts">
import { RouterView } from "vue-router";
import Toaster from "./components/Toaster.vue";
</script>

<style lang="scss" scoped>
// Route transition animation
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
