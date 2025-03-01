<template>
  <div class="overlay">
    <slot class="content" />
  </div>
</template>

<style lang="scss" scoped>
@use "@/assets/scss/color";

.overlay {
  z-index: 10;
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: color.$overlay0;
  // opacity: 0.5;
  // backdrop-filter: blur(5px);

  display: flex;
  justify-content: center;
  align-items: center;
}

.content {}
</style>
