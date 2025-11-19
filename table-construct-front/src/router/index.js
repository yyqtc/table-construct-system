import Vue from 'vue'
import VueRouter from 'vue-router'
import UploadView from '@/views/UploadView.vue'
import DisplayView from '@/views/DisplayView.vue'

Vue.use(VueRouter)

const routes = [
  {
    path: '/upload',
    name: 'UploadView',
    component: UploadView
  },
  {
    path: '/display',
    name: 'DisplayView',
    component: DisplayView
  },
  {
    path: '/',
    redirect: '/upload'
  }
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.VUE_APP_BASE_URL,
  routes
})

export default router
