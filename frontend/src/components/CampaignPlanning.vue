<template>
  <div>
    <h1 class="page-title"><span class="font-weight-light">Planning</span> {{campaignName}}</h1>
    <table v-if="campaign.entries">
      <tr>
        <th>Short Name</th>
        <th>Dataset</th>
        <th>Pileup</th>
        <th>Chain Tag</th>
        <th>Events</th>
        <th>Interested PWGs</th>
        <th>Comment</th>
        <th>Fragment</th>
      </tr>
      <tr v-for="entry in campaign.entries" :key="entry.dataset + entry.uid">
        <td :title="entry.uid">{{entry.short_name}} <span style="color:red" v-if="entry.broken">Not saved!</span></td>
        <td v-on:dblclick="startEditing($event, entry, 'dataset')">
          <template v-if="!entry.editing.dataset">{{entry.dataset}} <small style="color:red" @click="deleteEntry(entry);">delete</small></template>
          <input @blur="stopEditing(entry, 'dataset')"
                 v-if="entry.editing.dataset"
                 type="text"
                 v-model="entry.temporary.dataset">
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'pileup')">
          <template v-if="!entry.editing.pileup">{{entry.pileup}}</template>
          <input @blur="stopEditing(entry, 'pileup')"
                 v-if="entry.editing.pileup"
                 type="text"
                 v-model="entry.temporary.pileup">
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'chain_tag')">
          <template v-if="!entry.editing.chain_tag">{{entry.chain_tag}}</template>
          <input @blur="stopEditing(entry, 'chain_tag')"
                 v-if="entry.editing.chain_tag"
                 type="text"
                 v-model="entry.temporary.chain_tag">
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'events')">
          <template v-if="!entry.editing.events">{{entry.events}}</template>
          <input @blur="stopEditing(entry, 'events')"
                 v-if="entry.editing.events"
                 type="text"
                 v-model="entry.temporary.events">
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'interested_pwgs')">
          <template v-if="!entry.editing.interested_pwgs">{{entry.interested_pwgs}}</template>
          <input @blur="stopEditing(entry, 'interested_pwgs')"
                 v-if="entry.editing.interested_pwgs"
                 type="text"
                 v-model="entry.temporary.interested_pwgs">
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'comment')">
          <template v-if="!entry.editing.comment">{{entry.comment}}</template>
          <input @blur="stopEditing(entry, 'comment')"
                 v-if="entry.editing.comment"
                 type="text"
                 v-model="entry.temporary.comment">
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'fragment')">
          <template v-if="!entry.editing.fragment">{{entry.fragment}}</template>
          <input @blur="stopEditing(entry, 'fragment')"
                 v-if="entry.editing.fragment"
                 type="text"
                 v-model="entry.temporary.fragment">
        </td>
      </tr>
      <tr>
        <td colspan="8" style="border: none; background: #fafafa;">
        </td>
      </tr>
      <tr>
        <td>
          Add new
        </td>
        <td>
          <input type="text" v-model="newEntry.dataset">
        </td>
        <td>
          <input type="text" v-model="newEntry.pileup">
        </td>
        <td>
          <input type="text" v-model="newEntry.chain_tag">
        </td>
        <td>
          <input type="text" v-model="newEntry.events">
        </td>
        <td>
          <input type="text" v-model="newEntry.interested_pwgs">
        </td>
        <td>
          <input type="text" v-model="newEntry.comment">
        </td>
        <td>
          <input type="text" v-model="newEntry.fragment">
        </td>
      </tr>
      <tr>
        <td colspan="8">
          <v-btn small class="mr-1 mt-1" color="primary" @click="addEntry()">Add</v-btn>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'planning',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      campaignName: undefined,
      interestedPWG: undefined,
      campaign: {},
      newEntry: {},
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    this.campaignName = query.name;
    if (query.pwg && query.pwg.length) {
      this.interestedPWG = query.pwg.toUpperCase();
    }
    this.fetchCampaign();
    this.newEntry = {'dataset': '',
                     'pileup': '',
                     'chain_tag': '',
                     'events': '',
                     'interested_pwgs': this.interestedPWG ? this.interestedPWG : '',
                     'comment': '',
                     'fragment': ''};
  },
  methods: {
    addEntry: function() {
      let newEntry = this.makeCopy(this.newEntry);
      newEntry['campaign_uid'] = this.campaign.uid;
      let httpRequest = axios.post('api/planning/add_entry', newEntry);
      let component = this;
      httpRequest.then(response => {
        let entry = response.data.response;
        entry.editing = {};
        entry.temporary = {};
        entry.dirty = false;
        entry.broken = false;
        component.campaign.entries.push(entry);
        component.newEntry = {'dataset': '',
                              'pileup': '',
                              'chain_tag': '',
                              'events': '',
                              'interested_pwgs': component.interestedPWG ? component.interestedPWG : '',
                              'comment': '',
                              'fragment': ''};
      }).catch(error => {
        alert(error.response);
      });
    },
    updateEntry: function(entry) {
      let entryCopy = this.makeCopy(entry);
      entryCopy['campaign_uid'] = this.campaign.uid;
      let httpRequest = axios.post('api/planning/update_entry', entryCopy);
      let component = this;
      httpRequest.then(response => {
        Object.assign(entry, response.data.response);
        entry.broken = false;
      }).catch(error => {
        alert(error.response);
        entry.broken = true;
      });
    },
    deleteEntry: function(entry) {
      let entryCopy = this.makeCopy(entry);
      entryCopy['campaign_uid'] = this.campaign.uid;
      let httpRequest = axios.delete('api/planning/delete_entry', {data: entryCopy});
      let component = this;
      httpRequest.then(response => {
        component.campaign.entries = component.campaign.entries.filter(item => item.uid !== entry.uid);
      }).catch(error => {
        alert(error.response);
      });
    },
    fetchCampaign: function() {
      let component = this;
      let url = 'api/planning/get/' + this.campaignName; 
      if (this.interestedPWG) {
        url += '/' + this.interestedPWG;
      }
      axios.get(url).then(response => {
        let campaign = response.data.response;
        campaign.entries.forEach(element => {
          element.editing = {};
          element.temporary = {};
          element.dirty = false;
          element.broken = false;
        });
        component.$set(component, 'campaign', campaign);
      }).catch(error => {
        alert(error.response);
      });
    },
    startEditing: function(event, entry, attribute) {
      entry.temporary[attribute] = entry[attribute];
      this.$set(entry.editing, attribute, true);
      const target = event.target;
      this.$nextTick(() => {
        let input = target.querySelector('input');
        if (input) {
          input.focus();
        }
      })
    },
    stopEditing: function(entry, attribute) {
      entry.dirty = entry.dirty || (entry[attribute] != entry.temporary[attribute]);
      entry[attribute] = entry.temporary[attribute];
      this.$set(entry.editing, attribute, false);
      if (entry.dirty) {
        this.updateEntry(entry);
      }
    },
  }
}
</script>

