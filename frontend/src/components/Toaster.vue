<template>
  <div class="toaster">
    <template v-for="msg in errors">
      <Toast scheme="error" :msg="msg" />
    </template>
    <template v-for="msg in warnings">
      <Toast scheme="warn" :msg="msg" />
    </template>
    <template v-for="msg in infos">
      <Toast scheme="info" :msg="msg" />
    </template>
  </div>
</template>

<script lang="ts" setup>
import { warnings, errors, infos } from "@/scripts/toast";
import Toast from "./Toast.vue";
</script>

<style lang="scss" scoped>
.toaster {
  z-index: 100;
  position: fixed;
  top: 0;
  right: 0;
}
</style>
