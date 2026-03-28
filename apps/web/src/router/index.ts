import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Profile from '../views/Profile.vue'
import Steps from '../views/Steps.vue'
import StepCreate from '../views/StepCreate.vue'
import StepDetail from '../views/StepDetail.vue'
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
    {
      path: '/steps',
      name: 'steps',
      component: Steps,
    },
    {
      path: '/steps/create',
      name: 'step-create',
      component: StepCreate,
      meta: { requiresAuth: true },
    },
    {
      path: '/steps/:id',
      name: 'step-detail',
      component: StepDetail,
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
