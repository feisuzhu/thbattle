import { createRouter, createWebHistory } from 'vue-router'
import Main from '@/views/Main.vue'
import Login from '@/views/Login/Login.vue'
import Profile from '@/views/Profile/Profile.vue';
import Migrate from '@/views/Migrate/Migrate.vue';


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      component: Main,
      children: [
        {
          path: '',
          redirect: '/profile',
        },
        {
          path: 'profile',
          name: 'profile',
          component: Profile,
        },
        {
          path: 'migrate',
          name: 'migrate',
          component: Migrate,
        }
      ]

    },
    {
      path: '/login',
      name: 'login',
      component: Login,
    },
  ],
})

export default router
