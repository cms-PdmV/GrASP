<template>
  <div>
    <h1 class="page-title">GrASP</h1>
    <h3 style="text-align: center">Custom Table Generator</h3>
    <CustomTable :existingCampaigns="existingCampaigns"/>
    <h3 style="text-align: center">Existing Samples</h3>
    <table>
      <tr>
        <th>Campaign Name</th>
        <th :colspan="pwgs.length">Interested PWGs</th>
      </tr>
      <tr v-for="campaign in existingCampaigns" :key="campaign.name">
        <td>
          <a :href="'existing?name=' + campaign.name">{{campaign.name}}</a>
          <a v-if="role('administrator')" :title="'Edit ' + campaign.name" style="text-decoration: none;" :href="'existing_edit?name=' + campaign.name">&#128295;</a>
        </td>
        <td v-for="pwg in pwgs" :key="pwg">
          <a :href="'existing?name=' + campaign.name + '&pwg=' + pwg">{{pwg}}</a>
        </td>
      </tr>
      <tr v-if="role('production_manager')">
        <td :colspan="pwgs.length + 2">
          <a :href="'existing_edit'"><i>Add new campaign</i></a>
        </td>
      </tr>
    </table>
    <h3 style="text-align: center">User Tagged Samples</h3>
    <table>
      <tr>
        <th>Tag</th>
      </tr>
      <tr v-for="tag in userTags" :key="tag.name">
        <td>
          <a :href="'tags?name=' + tag.name">{{tag.name}}</a>
          <a v-if="role('administrator')" :title="'Edit ' + tag.name" style="text-decoration: none;" :href="'tag_edit?name=' + tag.name">&#128295;</a>
        </td>
      </tr>
      <tr v-if="role('user')">
        <td :colspan="pwgs.length + 2">
          <a :href="'tag_edit'"><i>Add new tag</i></a>
        </td>
      </tr>
    </table>
    <h3 style="text-align: center">GrASP Improvement</h3>
    <div style="text-align: center"><a href="https://github.com/cms-PdmV/GrASP/issues/new/choose">Report a bug or suggest a feature</a></div>
  </div>
</template>

<script>

import axios from 'axios'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import CustomTable from './CustomTableForm.vue'

export default {
  name: 'home',
  mixins: [
    roleMixin
  ],
  data () {
    return {
      existingCampaigns: [],
      userTags: [],
      pwgs: ['B2G', 'BPH', 'BTV', 'EGM', 'EXO', 'FSQ', 'HCA', 'HGC', 'HIG', 'HIN', 'JME', 'L1T', 'LUM', 'MUO', 'PPS', 'SMP', 'SUS', 'TAU', 'TOP', 'TRK', 'TSG'],
    }
  },
  created () {
    this.fetchObjectsInfo();
  },
  methods: {
    fetchObjectsInfo () {
      let component = this;
      axios.get('api/existing/get_all').then(response => {
        component.existingCampaigns = response.data.response;
      });
      axios.get('api/user_tag/get_all').then(response => {
        component.userTags = response.data.response;
      });
    },
  },
  components: {
    CustomTable
  }
}
</script>

