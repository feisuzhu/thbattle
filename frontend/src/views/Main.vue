<template>
  <Overlay v-if="loading">
    <Loading />
  </Overlay>
  <template v-else>
    <router-view />
  </template>
</template>

<script setup lang="ts">
import { RouterView } from "vue-router";

import Overlay from "@/components/Overlay.vue";
import Loading from "@/components/Loading.vue";
import { ref } from "vue";
import toast from "@/scripts/toast";

import { useRouter } from "vue-router";
import { useQuery } from "villus";
import { graphql } from "@/scripts/graphql";
import { queryString } from "@/scripts/utils";

async function requireLogin() {
  const loginToken = queryString("loginToken");

  if (loginToken) {
    const { data } = useQuery({
      query: graphql(
        "query ($token: String!) { login { token(token: $token) { token } } }"
      ),
      variables: { token: loginToken },
    });
    const token = data.value?.login?.token;
    if (token) {
      localStorage["token"] = token;
    }
  }

  return !!localStorage["token"];
}

//TODO:
const loading = ref(true);
const router = useRouter();

requireLogin()
  .then((logined) => {
    // if (!logined) router.replace(`/login`);
  })
  .catch((e) => toast.error(e))
  .finally(() => (loading.value = false));
</script>

<style lang="scss" scoped></style>
