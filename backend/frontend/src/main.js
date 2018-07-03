import Vue from 'vue'
import VueRouter from 'vue-router'

import Index from './Index.vue'

import Login from './view/Login.vue'
import Register from './view/Register.vue'

Vue.use(VueRouter)

new Vue({
  el: '#app',
  router: new VueRouter({
    routes: [
      {path: '/',         component: Login},
      {path: '/register', component: Register},
//      {path: '/about',    component: About},
//      {path: '/blogs',    component: BlogList},
//      {path: '/blog/:id', component: Blog},
//      {path: '/contacts', component: Contacts},
//      {path: '/episodes', component: Episodes},
//      {path: '/library',  component: Library},
//      {path: '/list',     component: List},
//      {path: '/list/:id', component: List},
//      {path: '/rules',    component: Rules},
//      {path: '/story',    component: Story},
    ],
    scrollBehavior (to, from, savedPosition) {
      return { x: 0, y: 0 }
    }
  }),
  components: { Index },
});
