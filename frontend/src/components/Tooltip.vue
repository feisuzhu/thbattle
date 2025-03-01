<template>
  <div class="tooltip" :style="{ '--tooltip-text': props.text }">
    <slot />
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{ text: string }>();
</script>

<style lang="scss" scoped>
.tooltip {
  position: relative;
  display: inline-block;
  border-bottom: 1px dotted black;

  &-text {
    visibility: hidden;
    width: 120px;
    background-color: black;
    color: #fff;
    text-align: center;
    padding: 5px 0;
    border-radius: 6px;

    position: absolute;
    z-index: 50;
  }

  &:hover &-text {
    visibility: visible;
  }
}
.tooltip:hover::before {
  content: var(--tooltip-text);
}
</style>
