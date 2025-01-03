<template>
  <nav>
  <img class="logo" src="@/assets/logo.png" alt="">
  </nav>
  <div class="greetings">
    <h1 class="green">{{ msg }}</h1>
    <h3>
      You’ve successfully created a project with
      <a href="https://vite.dev/" target="_blank" rel="noopener">Vite</a> +
      <a href="https://vuejs.org/" target="_blank" rel="noopener">Vue 3</a>. What's next?
    </h3>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  msg: string
}>()
</script>


<style scoped lang="scss">
nav {
  width: 100%;
  height: 62px;
  padding: 0 20px;
  background-color: var(--color-primary);

  .logo {
    height: 100%;
  }
}
</style>
