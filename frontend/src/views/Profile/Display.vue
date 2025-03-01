<template>
  <div class="card-profile">
    <div class="card-profile-r1">
      <div class="card-profile-r1-avatar">
        <Tooltip text="更换头像">
          <Avatar :src="profile.avatar" />
        </Tooltip>
      </div>
      <div class="card-profile-r1-profile">
        <span class="nickname">{{ profile.name }}</span>
        <div class="data">
          <span>游戏数：{{ profile.games }}</span>
          <span>逃跑数：{{ profile.drops }}</span>
          <span>等级：{{ profile.drops }}</span>
          <span>Bomb：{{ profile.drops }}</span>
          <span>Point：{{ profile.drops }}</span>
        </div>
      </div>
    </div>
    <textarea class="bio" type="text" maxlength="150" placeholder="留下你独特的签名~" :value="profile.bio"
      @change="updateBio" />
    <button class="btn-edit" @click="emit('edit')">编辑</button>
  </div>
</template>

<script lang="ts" setup>
import { useProfileStore } from "@/store/profile";
import Avatar from "@/components/Avatar.vue";
import Tooltip from "@/components/Tooltip.vue";

const profile = useProfileStore();
const emit = defineEmits(["edit"]);

async function updateBio() {
  //TODO:
}
</script>

<style lang="scss" scoped>
@use "@/assets/scss/color";

// Layout
.card-profile {
  margin: 24px;
  padding: 16px;

  border-radius: 12px;

  display: grid;
  grid-template-rows: 1fr 1fr;
  gap: 16px;

  &-r1 {
    display: flex;
    flex-direction: row;

    &-profile {
      padding: 12px;
    }
  }
}

// Style
.card-profile {
  background-color: color.$surface0;

  .bio {
    resize: none;
    outline: none;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;

    display: flow-root;
    padding: 8px;
    color: color.$text;
    background-color: color.$surface0;

    border: {
      style: none;
      width: 0px;
      color: none;
      radius: 8px;
    }

    transition-duration: 0.25s;
  }

  .bio:hover {
    background-color: color.$overlay0;
  }

  .bio:focus {
    background-color: color.$mantle;
  }
}

.nickname {
  border-bottom: {
    style: solid;
    width: thin;
    color: color.$mantle;
  }

  font: {
    size: 1.5rem;
    weight: bolder;
    family: "Fira Sans";
  }
}

.data {
  display: flex;
  gap: 8px;
  flex-flow: wrap;

  font: {
    size: small;
  }
}

.btn-edit {
  display: inline-block;
  width: fit-content;

  color: color.$base;
  background-color: color.$teal;
  cursor: pointer;

  border: {
    width: medium;
    color: color.$green;
    radius: 4px;
  }

  font: {
    family: "HYTMR", "Fira Sans";
    size: 1em;
    weight: bold;
  }

  text-shadow: 1px 1px 2px color.$text,
  0 0 1em color.$green,
  0 0 0.2em color.$green;
}
</style>
