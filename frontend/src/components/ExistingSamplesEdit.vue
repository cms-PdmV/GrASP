<template>
  <div>
    <h1 class="page-title" v-if="creatingNew"><span class="font-weight-light">Creating</span> new existing campaign</h1>
    <h1 class="page-title" v-else><span class="font-weight-light">Editing</span> {{campaignName}}</h1>
    <table v-if="campaign">
      <tr>
        <td>Name</td>
        <td><input type="text" v-model="campaign.name"></td>
      </tr>
    </table>
    <div style="text-align: center;">
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()">Save</v-btn>
      <v-btn small class="mr-1 mt-1" color="error" @click="cancel()">Cancel</v-btn>
    </div>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'existing_edit',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      campaignName: undefined,
      campaign: undefined,
      loading: true,
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
      this.campaign = {'name': ''};
    } else {
      this.loading = true;
      let component = this;
      axios.get('api/existing/get/' + this.campaignName).then(response => {
        component.campaign = response.data.response;
        component.loading = false
      }).catch(error => {
        component.loading = false;
        console.error(error);
      });
    }
  },
  methods: {
    save: function() {
      this.loading = true;
      let campaign = this.makeCopy(this.campaign);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/existing/create', campaign);
      } else {
        httpRequest = axios.post('api/existing/update', campaign);
      }
      let component = this;
      httpRequest.then(response => {
        component.loading = false;
        console.log('OK');
        console.log(response);
        window.location = 'existing?name=' + component.campaign.name;
      }).catch(error => {
        component.loading = false;
        console.error(error);
      });
    },
    cancel: function() {
      console.log('Cancel');
    },
  }
}
</script>
