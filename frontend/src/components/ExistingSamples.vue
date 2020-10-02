<template>
  <div>
    <h1 class="page-title"><span class="font-weight-light">Samples in</span> {{campaignName}}</h1>
    <div class="align-center" v-if="!campaign.entries">
      <img src="static/loading.gif" style="width: 150px; height: 150px;"/>
      <h3>Loading table...</h3>
    </div>
    <table v-if="campaign.entries" class="highlight-on-hover">
      <tr>
        <th>Short Name</th>
        <th>Dataset Name</th>
        <th>Root Request</th>
        <th>MiniAOD Request</th>
        <th>Chained Request</th>
        <th>Interested PWGs</th>
        <!-- <th>Notes</th> -->
      </tr>
      <tr v-for="entry in campaign.entries" :key="entry.dataset + entry.uid">
        <td>{{entry.short_name}}</td>
        <td><a :href="'https://cms-pdmv.cern.ch/mcm/requests?dataset_name=' + entry.dataset" target="_blank">{{entry.dataset}}</a></td>
        <td class="progress-cell">
          <div>
            <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.root_request" target="_blank">McM</a>
            <a :href="'https://cms-pdmv.cern.ch/pmp/historical?r=' + entry.root_request" target="_blank" class="ml-1">pMp</a>
            <template v-if="entry.root_request_output">
              <a :href="makeDASLink(entry.root_request_output)" target="_blank" class="ml-1">DAS</a>
            </template>
            <br>
            <small>Events:</small> {{entry.rootEventsNice}}
            <br>
            <small>Status:</small> {{entry.root_request_status}}
          </div>
          <div v-if="entry.root_request_total_events != 0"
               :class="'progress-background ' + entry.root_request_status + '-background'"
               :style="'width: ' + (entry.root_request_done_events / entry.root_request_total_events * 100) + '%;'">
          </div>
        </td>
        <td class="progress-cell">
          <template v-if="entry.miniaod.length">
            <div>
              <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.miniaod" target="_blank">McM</a>
              <a :href="'https://cms-pdmv.cern.ch/pmp/historical?r=' + entry.miniaod" target="_blank" class="ml-1">pMp</a>
              <template v-if="entry.miniaod_output">
                <a :href="makeDASLink(entry.miniaod_output)" target="_blank" class="ml-1">DAS</a>
              </template>
              <br>
              <small>Events:</small> {{entry.miniaodEventsNice}}
              <br>
              <small>Status:</small> {{entry.miniaod_status}}
              </div>
            <div v-if="entry.miniaod_total_events != 0"
                :class="'progress-background ' + entry.miniaod_status + '-background'"
                :style="'width: ' + (entry.miniaod_done_events / entry.miniaod_total_events * 100) + '%;'">
            </div>
          </template>
        </td>
        <td>
          <a :href="'https://cms-pdmv.cern.ch/mcm/chained_requests?prepid=' + entry.chained_request" target="_blank">{{entry.chain_tag}}</a>
        </td>
        <td v-on:dblclick="startEditing($event, entry, 'interested_pwgs')" class="align-center">
          <template v-if="!entry.editing.interested_pwgs">{{entry.interested_pwgs}}</template>
          <input @blur="stopEditing(entry, 'interested_pwgs')"
                 v-if="entry.editing.interested_pwgs"
                 type="text"
                 v-model="entry.temporary.interested_pwgs">
        </td>
        <!-- <td style="max-width: 300px" class="wrap">{{entry.notes}}</td> -->
      </tr>
    </table>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'existing',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      campaignName: undefined,
      interestedPWG: undefined,
      campaign: {},
      newEntry: {},
      sumPerChainTag: [],
      // Sum of all events
      sumTotal: 0,
      // Sum of all events with k, M, G suffix
      sumTotalNice: '',
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
                     'chain_tag': '',
                     'events': '',
                     'interested_pwgs': this.interestedPWG ? this.interestedPWG : '',
                     'comment': '',
                     'fragment': ''};
  },
  methods: {
    updateEntry: function(entry) {
      let entryCopy = this.makeCopy(entry);
      entryCopy['campaign_uid'] = this.campaign.uid;
      let httpRequest = axios.post('api/existing/update_entry', entryCopy);
      let component = this;
      httpRequest.then(response => {
        Object.assign(entry, response.data.response);
        component.processEntry(entry);
      }).catch(error => {
        console.error(error);
        alert(error.response);
        entry.broken = true;
      });
    },
    processEntry: function(entry) {
      // Add or set to default some attributes
      // and calculate number with SI suffix
      entry.editing = {};
      entry.temporary = {};
      entry.dirty = false;
      entry.broken = false;
      entry.rootDoneEventsNice = this.suffixNumber(entry.root_request_done_events);
      entry.rootTotalEventsNice = this.suffixNumber(entry.root_request_total_events);
      entry.miniaodDoneEventsNice = this.suffixNumber(entry.miniaod_done_events);
      entry.miniaodTotalEventsNice = this.suffixNumber(entry.miniaod_total_events);
      if (entry.root_request_status == 'submitted' || entry.root_request_status == 'done') {
        entry.rootEventsNice = entry.rootDoneEventsNice + '/' + entry.rootTotalEventsNice;
      } else {
        entry.rootEventsNice = entry.rootTotalEventsNice;
      }
      if (entry.miniaod_status == 'submitted' || entry.miniaod_status == 'done') {
        entry.miniaodEventsNice = entry.miniaodDoneEventsNice + '/' + entry.miniaodTotalEventsNice;
      } else {
        entry.miniaodEventsNice = entry.miniaodTotalEventsNice;
      }
    },
    fetchCampaign: function() {
      let component = this;
      let url = 'api/existing/get/' + this.campaignName; 
      if (this.interestedPWG) {
        url += '/' + this.interestedPWG;
      }
      axios.get(url).then(response => {
        let campaign = response.data.response;
        campaign.entries.forEach(element => {
          component.processEntry(element);
        });
        component.$set(component, 'campaign', campaign);
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

<style scoped>

td {
  white-space: nowrap;
  min-width: 100px;
  position: relative;
}

td.wide {
  min-width: 300px;
}

td.wrap {
  white-space: normal;
  line-break: anywhere;
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

.done-background {
  background-color: rgba(30, 150, 30, 0.18);
}

.submitted-background {
  background-color: rgba(0, 90, 255, 0.18);
}

.approved-background {
  width: 100% !important;
  background-color: rgba(240, 120, 0, 0.33);
}

.defined-background {
  width: 100% !important;
  background-color: rgba(220, 220, 0, 0.43);
}

.validation-background {
  width: 100% !important;
  background-color: rgba(255, 0, 255, 0.23);
}

.new-background {
  width: 100% !important;
  background-color: rgba(0, 0, 0, 0.1);
}

.progress-background {
  max-width: 100%;
  height: 100%;
  z-index: 1;
  position:absolute;
  top: 0;
  left: 0
}

td>div:first-child {
  position: relative;
  z-index: 2;
}

small {
  color: #5a5a5a;
}

</style>

