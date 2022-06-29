<template>
  <div>
    <h1 class="page-title">GrASP</h1>
    <h3>Dataset search</h3>
    <div style="max-width: 700px; margin: 0 auto; text-align: center;">
      <wild-search :campaignNames="campaigns"></wild-search>
    </div>
    <h3>File upload</h3>
    <div style="text-align: center;">
      <a :href="'samples?file=true&campaign=' + campaigns.join(',')">Upload file with dataset names</a>
    </div>
    <h3>Campaigns</h3>
    <table>
      <tr>
        <th>Name</th>
        <th :colspan="pwgs.length">Interested PWGs</th>
      </tr>
      <tr v-for="campaign in campaigns" :key="campaign">
        <td>
          <a :href="'samples?campaign=' + campaign">{{campaign}}</a>
          <span v-if="role('production_manager')" class="delete-button" :title="'Delete ' + campaign" @click="deleteCampaign(campaign)">&#10060;</span>
        </td>
        <td v-for="pwg in pwgs" :key="pwg">
          <a :href="'samples?campaign=' + campaign + '&pwgs=' + pwg">{{pwg}}</a>
        </td>
      </tr>
      <tr v-if="role('production_manager')">
        <td :colspan="pwgs.length + 2">
          <a :href="'campaign'"><i>Add new campaign</i></a>
        </td>
      </tr>
    </table>
    <h3>Tags</h3>
    <table>
      <tr>
        <th>Tag</th>
      </tr>
      <tr v-for="tag in tags" :key="tag">
        <td>
          <a :href="'samples?tags=' + tag">{{tag}}</a>
          <span v-if="role('production_manager')" class="delete-button" :title="'Delete ' + tag" @click="deleteTag(tag)">&#10060;</span>
        </td>
      </tr>
      <tr v-if="role('user')">
        <td :colspan="pwgs.length + 2">
          <a :href="'tag'"><i>Add new tag</i></a>
        </td>
      </tr>
    </table>
    <h3>GrASP Improvement</h3>
    <div style="text-align: center"><a href="https://github.com/cms-PdmV/GrASP/issues/new/choose">Report a bug or suggest a feature</a></div>
  </div>
</template>

<script>

import axios from 'axios'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import WildSearch from './WildSearch'

export default {
  name: 'home',
  mixins: [
    roleMixin,
  ],
  components: {
    WildSearch
  },
  data () {
    return {
      campaigns: [],
      tags: [],
      pwgs: ['B2G', 'BPH', 'BTV', 'EGM', 'EXO', 'FSQ', 'GEN', 'HCA', 'HGC', 'HIG', 'HIN', 'JME', 'L1T', 'LUM', 'MUO', 'PPS', 'SMP', 'SUS', 'TAU', 'TOP', 'TRK', 'TSG'],
    }
  },
  created () {
    this.fetchObjectsInfo();
  },
  methods: {
    fetchObjectsInfo () {
      let component = this;
      axios.get('api/campaigns/get_all').then(response => {
        component.campaigns = response.data.response;
      });
      axios.get('api/tags/get_all').then(response => {
        component.tags = response.data.response;
      });
    },
    deleteCampaign: function(campaignName) {
      if (confirm('Are you sure you want to remove campaign ' + campaignName)) {
        const component = this;
        axios.delete('api/campaigns/delete/' + campaignName).then(() => {
          component.fetchObjectsInfo();
        });
      }
    },
    deleteTag: function(tag) {
      if (confirm('Are you sure you want to remove tag ' + tag)) {
        const component = this;
        axios.delete('api/tags/delete/' + tag).then(() => {
          component.fetchObjectsInfo();
        });
      }
    }
  },
}
</script>

<style scoped>

.delete-button {
  cursor: pointer;
  font-size: 0.5em;
  margin-left: 4px;
}

h3 {
  text-align: center;
  margin-top: 20px;
  margin-bottom: 2px;
}

table {
  margin-bottom: 0px;
}

</style>
