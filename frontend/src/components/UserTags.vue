<template>
  <div>
    <h1 v-if="tag.entries" class="page-title">
      <span class="font-weight-light">Samples tagged</span> {{tag.name}}
      <template v-if="interestedPWG">
        <span class="font-weight-light">where</span> {{interestedPWG}} <span class="font-weight-light">is interested</span>
      </template>
    </h1>
    <div class="align-center mt-4" v-if="!tag.entries">
      <img :src="'static/loading' + getRandomInt(3) + '.gif'" style="width: 120px; height: 120px;"/>
      <h3>Loading table...</h3>
    </div>
    <div v-if="tag.entries" class="align-center">
      <RadioSelector :options="eventFilterOptions"
                    v-on:changed="onEventFilterUpdate"
                    class="mb-2">
        Events Filter:
      </RadioSelector>
    </div>
    <table v-if="tag.entries">
      <tr>
        <th>Short Name<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.short_name" @input="applyFilters()"></th>
        <th>Dataset Name<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.dataset" @input="applyFilters()"></th>
        <th>Root Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.root_request" @input="applyFilters()"></th>
        <th>MiniAOD Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.miniaod" @input="applyFilters()"></th>
        <th>NanoAOD Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.nanoaod" @input="applyFilters()"></th>
        <th>Chained Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.chained_request" @input="applyFilters()"></th>
        <!-- <th>Interested PWGs</th> -->
      </tr>
      <tr v-for="entry in entries" :key="entry.dataset + entry.uid">
        <td v-if="entry.rowspan.short_name > 0" :rowspan="entry.rowspan.short_name">{{entry.short_name}}</td>
        <td v-if="entry.rowspan.dataset > 0" :rowspan="entry.rowspan.dataset">
          <a :href="'https://cms-pdmv.cern.ch/mcm/requests?dataset_name=' + entry.dataset + '&member_of_tag=' + tag.name" target="_blank">{{entry.dataset}}</a>
        </td>
        <td v-if="entry.rowspan.root_request > 0" :rowspan="entry.rowspan.root_request" class="progress-cell">
          <div>
            <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.root_request" target="_blank">McM</a>
            <a :href="'https://cms-pdmv.cern.ch/pmp/historical?r=' + entry.root_request" target="_blank" class="ml-1">pMp</a>
            <template v-if="entry.root_request_output">
              <a :href="makeDASLink(entry.root_request_output)" target="_blank" class="ml-1">DAS</a>
            </template>
            <br>
            <small>Events: {{entry.rootEventsNice}}</small>
            <br>
            <small>Priority: {{entry.root_request_priority}}</small>
            <br>
            <small>Status: {{entry.root_request_status}}</small>
          </div>
          <div :class="'progress-background ' + entry.root_request_status + '-background'"
               :style="'width: ' + entry.rootPercentage + '%;'">
          </div>
        </td>
        <td v-if="entry.rowspan.miniaod > 0" :rowspan="entry.rowspan.miniaod" class="progress-cell">
          <template v-if="entry.miniaod.length">
            <div>
              <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.miniaod" target="_blank">McM</a>
              <a :href="'https://cms-pdmv.cern.ch/pmp/historical?r=' + entry.miniaod" target="_blank" class="ml-1">pMp</a>
              <template v-if="entry.miniaod_output">
                <a :href="makeDASLink(entry.miniaod_output)" target="_blank" class="ml-1">DAS</a>
              </template>
              <br>
              <small>Events: {{entry.miniaodEventsNice}}</small>
              <br>
              <small>Priority: {{entry.miniaod_priority}}</small>
              <br>
              <small>Status: {{entry.miniaod_status}}</small>
            </div>
            <div :class="'progress-background ' + entry.miniaod_status + '-background'"
                 :style="'width: ' + entry.miniaodPercentage + '%;'">
            </div>
          </template>
        </td>
        <td class="progress-cell">
          <template v-if="entry.nanoaod.length">
            <div>
              <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.nanoaod" target="_blank">McM</a>
              <a :href="'https://cms-pdmv.cern.ch/pmp/historical?r=' + entry.nanoaod" target="_blank" class="ml-1">pMp</a>
              <template v-if="entry.nanoaod_output">
                <a :href="makeDASLink(entry.nanoaod_output)" target="_blank" class="ml-1">DAS</a>
              </template>
              <br>
              <small>Events: {{entry.nanoaodEventsNice}}</small>
              <br>
              <small>Priority: {{entry.nanoaod_priority}}</small>
              <br>
              <small>Status: {{entry.nanoaod_status}}</small>
            </div>
            <div :class="'progress-background ' + entry.nanoaod_status + '-background'"
                 :style="'width: ' + entry.nanoaodPercentage + '%;'">
            </div>
          </template>
        </td>
        <td>
          <a :href="'https://cms-pdmv.cern.ch/mcm/chained_requests?prepid=' + entry.chained_request" target="_blank">{{entry.chain_tag}}</a>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import RadioSelector from './RadioSelector'

export default {
  name: 'existing',
  mixins: [
    utilsMixin,
    roleMixin
  ],
  components: {
    RadioSelector
  },
  data () {
    return {
      interestedPWG: undefined,
      tag: {},
      newEntry: {},
      eventFilterOptions: [[0, 'All'], [5e6, '5M+'], [10e6, '10M+'], [20e6, '20M+'], [50e6, '50M+']],
      eventsFilter: 0,
      entries: [], // Filtered entries,
      search: {
        short_name: undefined,
        dataset: undefined,
        root_request: undefined,
        miniaod: undefined,
        nanoaod: undefined,
        chained_request: undefined,
      }
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    let tagName = query.name;
    if (query.pwg && query.pwg.length) {
      this.interestedPWG = query.pwg.toUpperCase();
    }
    this.fetchTag(tagName);
  },
  methods: {
    updateEntry: function(entry) {
      let entryCopy = this.makeCopy(entry);
      entryCopy['tag_uid'] = this.tag.uid;
      let httpRequest = axios.post('api/user_tag/update_entry', entryCopy);
      let component = this;
      httpRequest.then(response => {
        Object.assign(entry, response.data.response);
        component.processEntry(entry);
      }).catch(error => {
        alert(error.response.data.message);
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
      entry.nanoaodDoneEventsNice = this.suffixNumber(entry.nanoaod_done_events);
      entry.nanoaodTotalEventsNice = this.suffixNumber(entry.nanoaod_total_events);
      if ((entry.root_request_status == 'submitted' || entry.root_request_status == 'done') && entry.root_request_output.length && entry.root_request_total_events) {
        entry.rootPercentage = entry.root_request_done_events / entry.root_request_total_events * 100;
        entry.rootEventsNice = entry.rootDoneEventsNice + '/' + entry.rootTotalEventsNice;
      } else {
        entry.rootPercentage = 100;
        entry.rootEventsNice = entry.rootTotalEventsNice;
      }

      if ((entry.miniaod_status == 'submitted' || entry.miniaod_status == 'done') && entry.miniaod_output.length && entry.miniaod_total_events) {
        entry.miniaodPercentage = entry.miniaod_done_events / entry.miniaod_total_events * 100;
        entry.miniaodEventsNice = entry.miniaodDoneEventsNice + '/' + entry.miniaodTotalEventsNice;
      } else {
        entry.miniaodPercentage = 100;
        entry.miniaodEventsNice = entry.miniaodTotalEventsNice;
      }

      if ((entry.nanoaod_status == 'submitted' || entry.nanoaod_status == 'done') && entry.nanoaod_output.length && entry.nanoaod_total_events) {
        entry.nanoaodPercentage = entry.nanoaod_done_events / entry.nanoaod_total_events * 100;
        entry.nanoaodEventsNice = entry.nanoaodDoneEventsNice + '/' + entry.nanoaodTotalEventsNice;
      } else {
        entry.nanoaodPercentage = 100;
        entry.nanoaodEventsNice = entry.nanoaodTotalEventsNice;
      }
    },
    fetchTag: function(tagName) {
      let component = this;
      let url = 'api/user_tag/get/' + tagName; 
      if (this.interestedPWG) {
        url += '/' + this.interestedPWG;
      }
      axios.get(url).then(response => {
        let tag = response.data.response;
        tag.entries.forEach(element => {
          component.processEntry(element);
        });
        component.mergeCells(tag.entries, ['short_name', 'dataset', 'root_request', 'miniaod'])
        component.$set(component, 'tag', tag);
      }).catch(error => {
        alert(error.response.data.message);
      });
    },
    mergeCells: function(list, attributes) {
      list.forEach(element => {
        element.rowspan = {};
        for (let attribute of attributes) {
          element.rowspan[attribute] = 1;
        }
      });
      for (let i = list.length - 1; i > 0; i--) {
        let thisEntry = list[i];
        let otherEntry = list[i - 1];
        for (let attribute of attributes) {
          if (thisEntry[attribute] !== otherEntry[attribute]) {
            break
          }
          otherEntry.rowspan[attribute] += thisEntry.rowspan[attribute];
          thisEntry.rowspan[attribute] = 0;
        }
      }
    },
    onEventFilterUpdate: function(events) {
      this.eventsFilter = events;
      this.applyFilters();
    },
    applyFilters: function() {
      let filteredEntries = this.tag.entries;
      if (this.eventsFilter != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.root_request_total_events >= this.eventsFilter);
      }
      for (let attribute in this.search) {
        if (this.search[attribute]) {
          const pattern = this.search[attribute].replace(/ /g, '*').replace(/\*/g, '.*');
          const regex = RegExp(pattern, 'i'); // 'i' for case insensitivity
          filteredEntries = filteredEntries.filter(entry => entry[attribute] != '' && regex.test(entry[attribute]));
        }
      }
      this.entries = filteredEntries;
      this.mergeCells(this.entries, ['short_name', 'dataset', 'root_request', 'miniaod']);
    },
  }
}
</script>

<style scoped>

td {
  white-space: nowrap;
  min-width: 100px;
  position: relative;
  line-height: 105%;
}

td.wrap {
  white-space: normal;
  line-break: anywhere;
}

.done-background {
  background-color: rgba(30, 150, 30, 0.18);
}

.submitted-background {
  background-color: rgba(0, 90, 255, 0.18);
}

.approved-background {
  background-color: rgba(240, 120, 0, 0.33);
}

.defined-background {
  background-color: rgba(220, 220, 0, 0.43);
}

.validation-background {
  background-color: rgba(255, 0, 255, 0.23);
}

.new-background {
  background-color: rgba(0, 0, 0, 0.1);
}

.progress-background {
  max-width: 100%;
  width: 100%;
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

</style>

