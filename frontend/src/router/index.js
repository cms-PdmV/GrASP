import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/components/Home'
import ExistingSamples from '@/components/ExistingSamples'
import ExistingSamplesEdit from '@/components/ExistingSamplesEdit'
import UserTags from '@/components/UserTags'
import UserTagsEdit from '@/components/UserTagsEdit'
import History from '@/components/History'
import qs from 'qs';


Vue.use(VueRouter)

const routes = [
  {
    path: '/',
    name: 'home',
    component: Home
  },
  {
    path: '/existing',
    name: 'existing',
    component: ExistingSamples
  },
  {
    path: '/existing_edit',
    name: 'existing_edit',
    component: ExistingSamplesEdit
  },
  {
    path: '/tags',
    name: 'tags',
    component: UserTags
  },
  {
    path: '/tag_edit',
    name: 'tag_edit',
    component: UserTagsEdit
  },
  {
    path: '/history',
    name: 'history',
    component: History
  },
]

const router = new VueRouter({
  mode: 'history',
  base: process.env.BASE_URL,
  stringifyQuery: query => {
    var result = qs.stringify(query);
    // Do not encode asterisks
    result = result.replace(/%2A/g, '*').replace(/%2F/g, '/').replace(/%21/g, '!').replace(/%2C/g, ',');
    return result ? ('?' + result) : '';
  },
  routes
})

export default router