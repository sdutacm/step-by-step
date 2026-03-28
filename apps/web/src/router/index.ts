import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Profile from '../views/Profile.vue'
import { getToken } from '../api/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'home',
      component: Home,
    },
    {
      path: '/profile',
      name: 'profile',
      component: Profile,
      meta: { requiresAuth: true },
    },
  ],
})

router.beforeEach((to, from, next) => {
  if (to.meta.requiresAuth && !getToken()) {
    next('/')
  } else {
    next()
  }
})

export default router
