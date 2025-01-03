<template>
  <Header />
  <RouterView />
</template>

<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import Header from './components/Header.vue'
</script>

<style>
--color-primary: #42b983;
</style>
