<script setup lang="ts"></script>

<template>
  <div class="spinner">
    <span>Loading...</span>
  </div>
</template>

<style lang="scss" scoped>
@use "@/assets/scss/color";

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }

  100% {
    transform: rotate(360deg);
  }
}

.spinner {
  border: 4px solid color.$surface1;
  border-top: 4px solid color.$mauve;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 0.65s linear infinite;

  span {
    visibility: hidden;
    width: 0px;
    height: 0px;
    margin: -1px;
    padding: 0px;
    white-space: nowrap;
    position: absolute;
    overflow: hidden;
    border-width: 0px;
  }
}
</style>
