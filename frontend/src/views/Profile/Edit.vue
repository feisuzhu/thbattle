<template>
  <div class="card">
    <div class="card-body">
      <div class="card-title"> 编辑资料 </div>
      <form>
        <c-tooltip content="更换头像" placement="right">
          <template #toggler="{ on }">
            <input type="file" ref='avatar' style="display: none;" />
            <c-link @click="avatar_ref?.click()">
              <c-avatar v-on="on" shape="rounded-circle" size="xl" :src="edited.avatar" />
            </c-link>
          </template>
        </c-tooltip>
        <!-- <c-row class="mb-3"> -->
        <!--   <c-col sm="10"> -->
        <!--     <c-form-input v-model="edited.name" floatingLabel="昵称" type="text" placeholder="为自己取一个名字吧~" /> -->
        <!--   </c-col> -->
        <!-- </c-row> -->

        <!-- <c-row> -->
        <!--   <fieldset class="row mb-3"> -->
        <!--     <legend class="col-form-label col-sm-2 pt-0">性别</legend> -->
        <!--     <c-col> -->
        <!--       <c-form-check type="radio" label="男" value="男" v-model="edited.gender" /> -->
        <!--     </c-col> -->
        <!--     <c-col> -->
        <!--       <c-form-check type="radio" label="女" value="女" v-model="edited.gender" /> -->
        <!--     </c-col> -->
        <!--     <c-col> -->
        <!--       <c-form-check type="radio" label="保密" value="保密" v-model="edited.gender" /> -->
        <!--     </c-col> -->
        <!--   </fieldset> -->
        <!-- </c-row> -->

        <c-row>
          <c-form-floating>
            <c-form-textarea v-model="edited.bio" placeholder="留下你独特的签名~" floatingLabel="个性签名"
              style="height: 100px"></c-form-textarea>
          </c-form-floating>
        </c-row>

        <c-button color="primary" type="submit" @click="onSubmit">保存</c-button>
      </form>
    </div>
  </div>
</template>

<script lang="ts" setup>
import { useMutation } from "villus";
import { useProfileStore } from "@/store/profile";
import { onMounted, useTemplateRef } from "vue";
import { graphql } from "@/scripts/graphql";

const stored = useProfileStore();

const edited = {
  // name: stored.name,
  bio: stored.profile.bio,
  avatar: stored.profile.avatar
}

const avatar_ref = useTemplateRef('avatar');
onMounted(() => {
  avatar_ref.value?.addEventListener('change', function () {
    const files = this.files;
    if (files) {
      const file = files[0].name;
      //TODO:
    }
  });
})

const { data, execute } = useMutation(graphql(`
    mutation($bio: String, $avatar: String) {
      PlUpdate()
    }
`))

async function onSubmit() {
  // TODO: Input validation: image size(<2MB) etc.
  execute(edited)
}
</script>



<style lang="scss" scoped></style 
