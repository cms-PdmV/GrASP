<template>
  <div>
    <h1 class="page-title">GrASP</h1>
    <h3 style="text-align: center">Future campaign planning</h3>
    <table>
      <tr>
        <th>Campaign Name</th>
        <th :colspan="pwgs.length">Interested PWGs</th>
      </tr>
      <tr v-for="campaign in futureCampaigns" :key="campaign.name">
        <td>
          <a :href="'planning?name=' + campaign.name">{{campaign.name}}</a>
          <a :title="'Edit ' + campaign.name" style="text-decoration: none;" :href="'planning_edit?name=' + campaign.name">&#128295;</a>
          <small v-if="!campaign.prefilled">Not yet updated</small>
        </td>
        <td v-for="pwg in pwgs" :key="pwg">
          <a :href="'planning?name=' + campaign.name + '&pwg=' + pwg">{{pwg}}</a>
        </td>
      </tr>
      <tr>
        <td :colspan="pwgs.length + 2">
          <a :href="'planning_edit'">Add new campaign</a>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>

import axios from 'axios'

export default {
  name: 'home',
  data () {
    return {
      futureCampaigns: [],
      pwgs: ['B2G', 'BPH', 'BTV', 'EGM', 'EXO', 'FSQ', 'HCA', 'HGC', 'HIG', 'HIN', 'JME', 'L1T', 'LUM', 'MUO', 'PPS', 'SMP', 'SUS', 'TAU', 'TOP', 'TRK', 'TSG'],
    }
  },
  created () {
    this.fetchObjectsInfo();
  },
  methods: {
    fetchObjectsInfo () {
      let component = this;
      axios.get('api/planning/get_all').then(response => {
        component.futureCampaigns = response.data.response;
      });
    },
  }
}
</script>

