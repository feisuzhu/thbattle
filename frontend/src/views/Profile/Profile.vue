<template>
  <DisplayProfile @edit="edit_v = !edit_v" />
  <Collapse :visible="edit_v">
    <EditProfile />
  </Collapse>
</template>

<script setup lang="ts">
import Collapse from "@/components/Collapse.vue";
import DisplayProfile from "./Display.vue";
import EditProfile from "./Edit.vue";
import { ref } from "vue";

const edit_v = ref(false);
</script>

<style lang="scss" scoped></style>
