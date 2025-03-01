<template>
  <div class="popup">
    <Popup />
  </div>
</template>

<script setup lang="ts">
import Popup from "./Popup.vue";
</script>

<style lang="scss" scoped>
.popup {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  width: 100%;
}
</style>
