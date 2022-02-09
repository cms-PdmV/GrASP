<template>
  <div>
    <h1 class="page-title" v-if="username">{{username}} <span class="font-weight-light">history</span></h1>
    <h1 class="page-title" v-else>All <span class="font-weight-light">history</span></h1>
    <table v-if="historyEntries">
      <tr>
        <th>Time</th>
        <th>Username</th>
        <th>Request</th>
        <th>Action</th>
        <th>Value</th>
      </tr>
      <tr v-for="entry in historyEntries" :key="entry.uid">
        <td>{{niceDate(entry.time)}}</td>
        <td>{{entry.user}}</td>
        <td>{{entry.prepid}}</td>
        <td>{{entry.action}}</td>
        <td>{{entry.value}}</td>
      </tr>
    </table>
  </div>
</template>

<script>

import axios from 'axios'
import dateFormat from 'dateformat'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'history',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      username: undefined,
      historyEntries: [],
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    if (query.name && query.name.length) {
      this.username = query.name;
    }
    let component = this;
    axios.get('api/system/history' + (this.username ? '/' + this.username : '')).then(response => {
      component.historyEntries = response.data.response;
    }).catch(error => {
      alert(error.response.data.message);
    });
  },
  methods: {
    niceDate: function (time) {
      return dateFormat(new Date(time * 1000), 'yyyy-mm-dd HH:MM:ss')
    },
  }
}
</script>
