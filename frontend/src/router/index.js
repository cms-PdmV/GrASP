import Vue from 'vue'
import VueRouter from 'vue-router'
import Home from '@/components/Home'
import Samples from '@/components/Samples'
import CampaignCreate from '@/components/CampaignCreate'
import TagCreate from '@/components/TagCreate'
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
    path: '/samples',
    name: 'samples',
    component: Samples
  },
  {
    path: '/campaign',
    name: 'campaign',
    component: CampaignCreate
  },
  {
    path: '/tag',
    name: 'tag',
    component: TagCreate
  },
  {
    path: '/history',
    name: 'history',
    component: History
  },
  {
    path: '/*',
    beforeEnter (to) {
      let newQuery = [];
      let path = to.path;
      let query = to.query;
      if (path == '/existing') {
        if (query.name) {
          newQuery.push(`campaign=${query.name}`)
        }
        if (query.pwg) {
          newQuery.push(`pwgs=${query.pwg}`)
        }
      } else if (path == '/tags') {
        if (query.name) {
          newQuery.push(`tags=${query.name}`)
        }
      }

      for (let key in query) {
        if (key == 'name' || key == 'pwg') {
          continue
        }
        let value = query[key];
        if (key == 'miniaod_version' || key == 'nanoaod_version') {
          value = value.replace('MiniAOD', '').replace('NanoAOD', '')
        }
        if (key == 'root_request') {
          key = 'root';
        }
        newQuery.push(`${key}=${value}`);
      }
      window.location = 'samples' + (newQuery.length ? '?' : '') + newQuery.join('&')
    }
  }
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
