<template>
  <div :class="['toast', 'toast-' + props.scheme]">
    <template v-if="typeof msg === 'string'"> </template>
    <template v-else>
      <div class="toast-header">
        <img :src="icon" width="24" height="24" />
        <span>{{ msg.title }}</span>
        <small>{{ msg.subTitle }}</small>
        <button type="button" class="btn-close" aria-label="Close" />
      </div>
      <div class="toast-body">
        {{ msg.content }}
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { Message } from "@/scripts/toast";
const props = defineProps<{
  scheme: "error" | "warn" | "info";
  msg: Message;
}>();
const icon =
  props.scheme === "error" ? "@/assets/error.svg":
  props.scheme === "warn"  ? "@/assets/warn.svg" :
  props.scheme === "info"  ? "@/assets/info.svg" :
  "";
</script>

<style lang="scss" scoped></style>
