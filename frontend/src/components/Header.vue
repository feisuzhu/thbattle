<template>
  <header role="banner">
    <nav class="nav">
      <img class="nav-brand" src="@/assets/logo.png" alt="" />
      <div class="nav-items">
        <!-- <ul> -->
        <!-- <li> -->
        <a class="nav-items-item" @click=""> 个人资料 </a>
        <!-- </li> -->
        <!-- <li> -->
        <a class="nav-items-item" @click="router.push('/user/0/migrate')">
          论坛迁移
        </a>
        <!-- </li> -->
        <!-- <li> -->
        <a class="nav-items-item" @click="router.push('/user/0/profile')">
          Go to profile
        </a>
        <!-- </li> -->
        <!-- <li> -->
        <a class="nav-items-item" @click="router.push('/login')">
          Go to login
        </a>
        <!-- </li> -->
        <!-- </ul> -->
      </div>
    </nav>
  </header>
</template>

<script setup lang="ts">
import router from "@/router";
</script>

<style scoped lang="scss">
@use "@/asstes/scss/color";

.nav {
  width: 100%;
  height: 62px;
  background-color: color.$mantle;
  // background-color: color.$surface0;

  border-bottom-color: color.$crust;
  // border-bottom-color: color.$surface1;
  border-bottom-style: solid;
  border-bottom-width: 2px;

  display: flex;
  flex-direction: row;

  position: fixed;

  &-brand {
    height: 100%;
    margin: 0 20px;
  }

  &-items {
    &-item {
      cursor: pointer;
      color: color.$text;

      font: {
        size: 1.3rem;
        weight: bolder;
      }

      margin: 0 20px;
    }
  }
}
</style>
