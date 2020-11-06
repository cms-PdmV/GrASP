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
      <v-btn small class="mr-1 mt-1" color="error" v-if="!creatingNew" @click="deleteCampaign()">Delete</v-btn>
    </div>
    <v-dialog v-model="dialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">
          {{dialog.title}}
        </v-card-title>
        <v-card-text>
          <span v-html="dialog.description"></span>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="dialog.cancel" @click="dialog.cancel">
            Cancel
          </v-btn>
          <v-btn small class="mr-1 mb-1" color="error" @click="dialog.ok">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
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
      dialog: {
        visible: false,
        title: '',
        description: '',
        cancel: undefined,
        ok: undefined,
      },
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
      httpRequest.then(() => {
        window.location = 'planning?name=' + component.campaign.name;
      }).catch(error => {
        alert(error.response.data.message);
      });
    },
    clearDialog: function() {
      this.dialog.visible = false;
      this.dialog.title = '';
      this.dialog.description = '';
      this.dialog.ok = function() {};
      this.dialog.cancel = function() {};
    },
    deleteCampaign: function() {
      let component = this;
      this.dialog.title = "Delete " + this.campaignName + " campaign?";
      this.dialog.description = "Are you sure you want to delete " + this.campaignName + " and all it's entries from GrASP?";
      this.dialog.ok = function() {
        let campaign = component.makeCopy(component.campaign);
        axios.delete('api/planning/delete', {data: campaign}).then(() => {
          component.clearDialog();
          window.location = '';
        }).catch(error => {
          alert(error.response.data.message);
        });
      }
      this.dialog.cancel = this.clearDialog;
      this.dialog.visible = true;
    },
  }
}
</script>

<style scoped>

input {
  min-width: 300px;
}

</style>