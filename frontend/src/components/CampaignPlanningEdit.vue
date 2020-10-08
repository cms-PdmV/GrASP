<template>
  <div>
    <h1 class="page-title" v-if="creatingNew"><span class="font-weight-light">Creating</span> new campaign plan</h1>
    <h1 class="page-title" v-else><span class="font-weight-light">Editing</span> {{campaignName}} <span class="font-weight-light">plan</span></h1>
    <table v-if="campaign">
      <tr>
        <td>Name</td>
        <td><input type="text" v-model="campaign.name"></td>
      </tr>
      <tr>
        <td>Reference</td>
        <td><input type="text" v-model="campaign.reference"></td>
      </tr>
    </table>
    <div style="text-align: center;">
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()">Save</v-btn>
    </div>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'planning_edit',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      campaignName: undefined,
      campaign: undefined,
      creatingNew: true,
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    if (query.name && query.name.length) {
      this.campaignName = query.name;
    } else {
      this.campaignName = '';
    }
    this.creatingNew = this.campaignName.length == 0;
    if (this.creatingNew) {
      this.campaign = {'name': '', 'reference': ''};
    } else {
      let component = this;
      axios.get('api/planning/get/' + this.campaignName).then(response => {
        component.campaign = response.data.response;
      }).catch(error => {
        console.error(error);
        alert(error.response.data.message);
      });
    }
  },
  methods: {
    save: function() {
      let campaign = this.makeCopy(this.campaign);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/planning/create', campaign);
      } else {
        httpRequest = axios.post('api/planning/update', campaign);
      }
      let component = this;
      httpRequest.then(response => {
        window.location = 'planning?name=' + component.campaign.name;
      }).catch(error => {
        console.error(error);
        alert(error.response.data.message);
      });
    },
  }
}
</script>

<style scoped>

input {
  min-width: 300px;
}

</style>