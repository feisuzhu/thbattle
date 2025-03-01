<template>
  <div class="avatar" @click="fileInput?.click()">
    <input type="file" accept=".png, .jpg, .jpeg, .webp" ref="file-input" style="display: none" />
    <picture>
      <source type="image/webp" :srcset="props.src" />
      <img :src="props.src" />
    </picture>
  </div>
</template>

<script setup lang="ts">
import { onMounted, useTemplateRef } from "vue";

const props = defineProps<{ src: string }>();

const fileInput = useTemplateRef("file-input");
onMounted(() => {
  fileInput.value?.addEventListener("change", function () {
    const files = this.files;
    if (files) {
      const file = files[0];
      //TODO:
    }
  });
});
</script>

<style lang="scss" scoped>
@use "@/assets/scss/color";

.avatar {
  cursor: pointer;

  line-height: 0;
  display: inline-block; // remove line-height
  margin: 5px;
  border: 4px solid color.$mantle;
  border-radius: 50%;
  transition: linear 0.25s;
  height: 128px;
  width: 128px;
}

.avatar:hover {
  transition: ease-out 0.2s;
  border: 4px solid color.$crust;
  -webkit-transition: ease-out 0.2s;
}

.avatar {
  color: transparent;

  img,
  source {
    border-radius: 50%;
    height: 100%;
    width: 100%;
  }
}
</style>
