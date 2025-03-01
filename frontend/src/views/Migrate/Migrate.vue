<template>
  <div class="popup">
    <Form />
  </div>
</template>

<script setup lang="ts">
import Form from "./Form.vue";
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
