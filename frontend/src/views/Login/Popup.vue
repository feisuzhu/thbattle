<template>
  <div class="popup">
    <article class="card">
      <header class="card-title">
        <h2>需要登录</h2>
      </header>
      <div class="card-content">
        <p>请在游戏中进行登录！</p>
      </div>
      <button @click="OpenTHBClient()">打开THB客户端</button>
    </article>
  </div>
</template>

<script setup lang="ts">
function OpenTHBClient() {
  // TODO: Require client registers URL scheme
  window.location.replace("thbattle://");
}
</script>

<style lang="scss" scoped>
@use "@/assets/scss/color";

.popup {
  position: fixed;
  z-index: 20;
  width: 90%;
}

.card {
  display: grid;
  grid-template-rows: minmax(1fr 90vw), minmax(2fr 90vw), minmax(1fr 90vw);
  row-gap: 16px;
  justify-items: center;
  align-items: center;

  // max-width: 90vw;
  width: 90%;

  @media (min-width: 640px) {
    width: 364px;
  }

  // height: 440px;

  background-color: color.$surface0;

  box-shadow: 0px 2px 20px -3px rgba(#000000, 2);

  line-height: 24px;

  border: {
    style: solid;
    width: 2px;
    color: color.$surface1;
    // radius: 12px;
    radius: 0.75rem;
  }

  padding: {
    left: 24px;
    right: 24px;
    bottom: 24px;
    top: 24px;
  }
}

button {
  $bg-color: color.$mauve;
  $border-color: darken($bg-color, 5%);
  $text-color: color.$base;
  // $text: color.$crust;

  background-color: $bg-color;
  color: $text-color;

  font: {
    family: "Fira Sans";
    size: 0.75em;
    // weight: bolder;
  }

  border: {
    //TODO:
    style: solid;
    color: $border-color;
    radius: 24px;
    top-width: 2px;
    left-width: 2px;
    right-width: 2px;
    bottom-width: 4px;
  }

  &:hover {
    color: darken($text-color, 5%);
    background-color: darken($bg-color, 5%);

    border: {
      color: darken($border-color, 5%);
    }
  }

  &:active {
    transform: scale(95%, 95%);
    transition-duration: 0.2s;

    // border-width: 2px;
    // transition-duration: 0.1s;
  }
}
</style>
