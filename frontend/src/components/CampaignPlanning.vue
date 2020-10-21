<template>
  <div>
    <h1 v-if="campaign.entries" class="page-title">
      <span class="font-weight-light">Planning</span> {{campaign.name}}
      <template v-if="interestedPWG.length.length">
        <span class="font-weight-light">where</span> {{interestedPWG}} <span class="font-weight-light">is interested</span>
      </template>
    </h1>
    <h3 class="page-title" v-if="campaign && campaign.reference && campaign.reference.length"><span class="font-weight-light">Reference:</span> {{campaign.reference}}</h3>
    <div class="align-center" v-if="!campaign.entries">
      <img src="static/loading.gif" style="width: 150px; height: 150px;"/>
      <h3>Loading table...</h3>
    </div>
    <div v-if="campaign.entries" class="align-center">
      <RadioSelector :options="eventFilterOptions"
                    v-on:changed="onEventFilterUpdate"
                    class="mb-2">
        Events filter:
      </RadioSelector>
    </div>
    <table v-if="campaign.entries" class="highlight-on-hover">
      <tr>
        <th>Short Name</th>
        <th>In Reference Campaign</th>
        <th>In Planned Campaign</th>
        <th>Dataset</th>
        <th>Chain Tag</th>
        <th>Events</th>
        <th>Interested PWGs</th>
        <th>Comment</th>
        <th>Fragment</th>
      </tr>
      <tr v-for="entry in entries" :key="entry.dataset + entry.uid">
        <td :title="entry.uid">{{entry.short_name}} <span class="red" v-if="entry.broken">Not saved!</span></td>
        <td class="align-center">
          <template v-if="entry.in_reference.length">
            <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.in_reference" target="_blank">{{entry.in_reference}}</a>
          </template>
          <template v-else>
            &#10799;
          </template>
        </td>
        <td class="align-center">
          <template v-if="entry.in_target.length">
            <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.in_target" target="_blank">{{entry.in_target}}</a>
          </template>
          <template v-else>
            &#10799;
          </template>
        </td>
        <td v-on:dblclick="role('user') && startEditing($event, entry, 'dataset')">
          <template v-if="!entry.editing.dataset">
            {{entry.dataset}}
            <span v-if="userInfo.role_index >= 1"
                  class="pointer show-on-hover"
                  @click="deleteEntry(entry);"
                  title="Delete this entry from planning table">&#10060;</span>
          </template>
          <input @blur="stopEditing(entry, 'dataset')"
                 v-if="entry.editing.dataset"
                 type="text"
                 v-model="entry.temporary.dataset">
        </td>
        <td v-on:dblclick="role('user') && startEditing($event, entry, 'chain_tag')">
          <template v-if="!entry.editing.chain_tag">{{entry.chain_tag}}</template>
          <input @blur="stopEditing(entry, 'chain_tag')"
                 v-if="entry.editing.chain_tag"
                 type="text"
                 v-model="entry.temporary.chain_tag">
        </td>
        <td v-on:dblclick="role('user') && startEditing($event, entry, 'events')" class="align-right">
          <template v-if="!entry.editing.events">{{entry.niceEvents}}</template>
          <input @blur="stopEditing(entry, 'events')"
                 v-if="entry.editing.events"
                 type="text"
                 v-model="entry.temporary.events">
        </td>
        <td v-on:dblclick="role('user') && startEditing($event, entry, 'interested_pwgs')" class="align-center">
          <template v-if="!entry.editing.interested_pwgs">{{entry.interested_pwgs}}</template>
          <input @blur="stopEditing(entry, 'interested_pwgs')"
                 v-if="entry.editing.interested_pwgs"
                 type="text"
                 v-model="entry.temporary.interested_pwgs">
        </td>
        <td v-on:dblclick="role('user') && startEditing($event, entry, 'comment')" class="wrap">
          <template v-if="!entry.editing.comment">{{entry.comment}}</template>
          <input @blur="stopEditing(entry, 'comment')"
                 v-if="entry.editing.comment"
                 type="text"
                 v-model="entry.temporary.comment">
        </td>
        <td v-on:dblclick="role('user') && startEditing($event, entry, 'fragment')">
          <template v-if="!entry.editing.fragment">{{entry.fragment}}</template>
          <input @blur="stopEditing(entry, 'fragment')"
                 v-if="entry.editing.fragment"
                 type="text"
                 v-model="entry.temporary.fragment">
        </td>
      </tr>
      <tr v-for="sum in sumPerChainTag" :key="sum[0]">
        <td class="hidden-cell"></td>
        <td class="hidden-cell"></td>
        <td class="hidden-cell"></td>
        <td class="hidden-cell"></td>
        <td class="opaque"><i>Total {{sum[0]}}</i></td>
        <td class="opaque align-right"><b :title="sum[1]">{{sum[2]}}</b></td>
      </tr>
      <tr>
        <td class="hidden-cell"></td>
        <td class="hidden-cell"></td>
        <td class="hidden-cell"></td>
        <td class="hidden-cell"></td>
        <td><b>Total</b></td>
        <td class="align-right"><b :title="sumTotal[1]">{{sumTotal[2]}}</b></td>
      </tr>
    </table>
    <template v-if="campaign.entries">
      <h3 class="page-title">Add New Entry</h3>
      <table class="mb-1">
        <tr>
          <th>Dataset</th>
          <th>Chain Tag</th>
          <th>Events</th>
          <th>Interested PWGs</th>
          <th>Comment</th>
          <th>Fragment</th>
        </tr>
        <tr>
          <td class="wide">
            <input type="text" v-model="newEntry.dataset" placeholder="E.g. ZZ_TuneCP5_13TeV-pythia8">
          </td>
          <td>
            <input type="text" v-model="newEntry.chain_tag" placeholder="E.g. Premix">
          </td>
          <td>
            <input type="text" v-model="newEntry.events" placeholder="Number of events">
          </td>
          <td class="wide">
            <input type="text" v-model="newEntry.interested_pwgs" placeholder="Comma separated, e.g. PPD,EXO,...">
          </td>
          <td class="wide">
            <input type="text" v-model="newEntry.comment" placeholder="Freeform comment">
          </td>
          <td class="wide">
            <input type="text" v-model="newEntry.fragment" placeholder="Link to a fragment">
          </td>
        </tr>
      </table>
      <div class="align-center mb-4">
        <v-btn small class="mr-1 mt-1" color="primary" @click="addEntry()">Add entry</v-btn>
      </div>
    </template>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import RadioSelector from './RadioSelector'

export default {
  name: 'planning',
  mixins: [
    utilsMixin,
    roleMixin
  ],
  components: {
    RadioSelector
  },
  data () {
    return {
      campaign: {},
      interestedPWG: '',
      newEntry: {},
      sumPerChainTag: [],
      sumTotal: [],
      eventFilterOptions: [[0, 'All'], [5e6, '5M+'], [10e6, '10M+'], [20e6, '20M+'], [50e6, '50M+']],
      eventsFilter: 0,
      entries: [], // Filtered entries
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    let campaignName = query.name;
    if (query.pwg && query.pwg.length) {
      this.interestedPWG = query.pwg.toUpperCase();
    }
    this.newEntry = this.getNewEntry();
    this.fetchCampaign(campaignName);
  },
  methods: {
    addEntry: function() {
      let newEntry = this.makeCopy(this.newEntry);
      newEntry['campaign_uid'] = this.campaign.uid;
      let component = this;
      axios.post('api/planning/add_entry', newEntry).then(response => {
        let entry = response.data.response;
        component.processEntry(entry);
        component.campaign.entries.push(entry);
        component.newEntry = component.getNewEntry();
        component.applyFilters();
      }).catch(error => {
        console.error(error);
        alert(error.response);
      });
    },
    updateEntry: function(entry) {
      let entryCopy = this.makeCopy(entry);
      entryCopy['campaign_uid'] = this.campaign.uid;
      let component = this;
      axios.post('api/planning/update_entry', entryCopy).then(response => {
        Object.assign(entry, response.data.response);
        component.processEntry(entry);
        component.applyFilters();
      }).catch(error => {
        console.error(error);
        alert(error.response);
        entry.broken = true;
      });
    },
    deleteEntry: function(entry) {
      if (confirm("Are you sure you want to delete " + entry.dataset + " " + entry.chain_tag + " with " + entry.events + " events ?")) {
        let entryCopy = this.makeCopy(entry);
        entryCopy['campaign_uid'] = this.campaign.uid;
        let component = this;
        axios.delete('api/planning/delete_entry', {data: entryCopy}).then(response => {
          component.campaign.entries = component.campaign.entries.filter(item => item.uid !== entry.uid);
          component.applyFilters();
        }).catch(error => {
          console.error(error);
          alert(error.response);
          entry.broken = true;
        });
      }
    },
    getNewEntry: function() {
      return {'dataset': '',
              'chain_tag': '',
              'events': '',
              'interested_pwgs': this.interestedPWG,
              'comment': '',
              'fragment': ''}
    },
    processEntry: function(entry) {
      // Add or set to default some attributes
      // and calculate number with SI suffix
      entry.editing = {};
      entry.temporary = {};
      entry.broken = false;
      entry.niceEvents = this.suffixNumber(entry.events);
    },
    applyFilters: function() {
      let filteredEntries = this.campaign.entries;
      if (this.eventsFilter != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.events >= this.eventsFilter);
      }
      this.entries = filteredEntries;
      this.recalculateChainTagSums();
    },
    fetchCampaign: function(campaignName) {
      let component = this;
      let url = 'api/planning/get/' + campaignName;
      if (this.interestedPWG.length) {
        url += '/' + this.interestedPWG;
      }
      axios.get(url).then(response => {
        let campaign = response.data.response;
        campaign.entries.forEach(element => {
          component.processEntry(element);
        });
        component.$set(component, 'campaign', campaign);
        component.applyFilters();
      }).catch(error => {
        console.error(error);
        alert(error.response);
      });
    },
    startEditing: function(event, entry, attribute) {
      entry.temporary[attribute] = entry[attribute];
      this.$set(entry.editing, attribute, true);
      const target = event.target;
      const width = target.getBoundingClientRect().width + 1;
      this.$nextTick(() => {
        let input = target.querySelector('input');
        if (input) {
          input.style.width = width + 'px';
          input.focus();
        }
      })
    },
    stopEditing: function(entry, attribute) {
      this.$set(entry.editing, attribute, false);
      if (entry[attribute] == entry.temporary[attribute]) {
        // Value not updated
        return
      }
      entry[attribute] = entry.temporary[attribute];
      this.updateEntry(entry);
    },
    recalculateChainTagSums: function() {
      let sums = {};
      let total = 0;
      this.entries.forEach(el => {
        let tag = el.chain_tag === '' ? '<unchained>' : el.chain_tag;
        if (!(tag in sums)) {
          sums[tag] = 0;
        }
        sums[tag] += el.events;
        total += el.events;
      });
      // Convert to a list of two-element lists and sort desc
      sums = Object.entries(sums).sort((a, b) => b[1] - a[1]);
      // Add nice number to each item in the list
      sums.forEach(el => {
        el.push(this.suffixNumber(el[1]));
      });
      this.sumPerChainTag = sums;
      this.sumTotal = ['Total', total, this.suffixNumber(total)];
    },
    onEventFilterUpdate: function(events) {
      this.eventsFilter = events;
      this.applyFilters();
    },
  }
}
</script>

<style scoped>

td {
  white-space: nowrap;
  min-width: 100px;
}

td.wide {
  min-width: 300px;
}

td.wrap {
  white-space: normal;
}

.opaque {
  opacity: 0.6;
}

.show-on-hover {
  opacity: 0;
}

tr:hover .show-on-hover {
  opacity: 1;
}

</style>

