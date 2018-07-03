<template>
  <div>
    <header-section></header-section>
    <router-view></router-view>
    <footer-section></footer-section>
  </div>
</template>

<style lang="sass">
@import "~bulma/bulma.sass";
@import "~@fortawesome/fontawesome-free/css/all.css";
</style>

<script>
import FooterSection from '~/components/footer/Footer.vue'
import HeaderSection from '~/components/header/Header.vue'
import { Q } from '~/utils.js'
import Store from '~/store.js'

export default {
  name: 'Index',
  components: { HeaderSection, FooterSection },
  data() {
    return {
        store: Store,
    }
  },
  mounted: function() {
    Store.refreshAccount();
  },
}
</script>
