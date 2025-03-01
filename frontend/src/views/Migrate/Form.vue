<template>
  <form class="card">
    <header class="card-title">
      <h1>论坛迁移</h1>
    </header>
    <div>
      <label for="account">账号 </label><input type="text" name="account" id="account" placeholder="UID/用户名/Email"
        v-model="inputs.account" required />
    </div>
    <div>
      <label for="password">密码 </label><input type="password" name="password" id="password" v-model="inputs.password"
        required />
    </div>
    <div>
      <input type="checkbox" name="use-old-name" id="use-old-name" v-model="inputs.migrateName" checked />
      <label for="use-old-name">使用旧昵称（覆盖当前昵称）</label>
    </div>
    <button type="button" @click="submit">登录</button>
  </form>
</template>

<script setup lang="ts">
import { useMutation } from "villus";
import { reactive } from "vue";

const inputs = reactive({
  account: "",
  password: "",
  migrateName: false,
});
const BindForum = `
mutation ($account:String!, $password:String!, migrateName: Boolean!){
  PlBindForum(account:$account, password:$password, migrateName:$migrateName)
}`;
const { execute } = useMutation(BindForum);

// TODO: Validation check
async function submit() {
  await execute(inputs);
}
</script>

<style lang="scss" scoped>
@use "@/assets/scss/color";

.card {
  display: grid;
  grid-template-rows:
    minmax(1fr 90vw),
    minmax(1fr 90vw),
    minmax(1fr 90vw),
    minmax(1fr 90vw),
    minmax(1fr 90vw);
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
</style>
