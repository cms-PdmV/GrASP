<template>
  <div>
    <h1 v-if="campaign.entries" class="page-title">
      <span class="font-weight-light">Samples in</span> {{campaign.name}}
      <template v-if="interestedPWG">
        <span class="font-weight-light">where</span> {{interestedPWG}} <span class="font-weight-light">is interested</span>
      </template>
    </h1>
    <div class="align-center mt-4" v-if="!campaign.entries">
      <img :src="'static/loading' + getRandomInt(3) + '.gif'" style="width: 120px; height: 120px;"/>
      <h3>Loading table...</h3>
    </div>
    <div class="align-center mb-4" v-if="undoStack.length || redoStack.length">
    <v-btn class="normal ma-1" small :disabled="!undoStack.length" @click="undoEvent">Undo</v-btn>
    <v-btn class="normal ma-1" small :disabled="!redoStack.length" @click="redoEvent">Redo</v-btn>
    </div>
    <div v-if="campaign.entries" class="align-center">
      <div class="ml-1 mr-1" style="display: inline-block">
        Events Filter:
        <template v-for="eventsPair in eventFilterOptions">
          <a :key="eventsPair[0]"
             class="ml-1 mr-1"
             :title="'Show samples with > ' + eventsPair[0] + ' events'"
             @click="onEventFilterUpdate(eventsPair[0])"
             :class="eventsPair[0] == eventsFilter ? 'bold-text' : ''">{{eventsPair[1]}}</a>
        </template>
      </div>
      |
      <div class="ml-1 mr-1" style="display: inline-block">
        MiniAOD Filter:
        <template v-for="miniaodPair in miniaodVersionFilterOptions">
          <a :key="miniaodPair[0]"
             class="ml-1 mr-1"
             :title="'Show samples with ' + miniaodPair[0]"
             @click="onMiniAODFilterUpdate(miniaodPair[0])"
             :class="miniaodPair[0] == miniaodVersionFilter ? 'bold-text' : ''">{{miniaodPair[1]}}</a>
        </template>
      </div>
      |
      <div class="ml-1 mr-1" style="display: inline-block">
        NaonoAOD Filter:
        <template v-for="nanoaodPair in nonoaodVersionFilterOptions">
          <a :key="nanoaodPair[0]"
             class="ml-1 mr-1"
             :title="'Show samples with ' + nanoaodPair[0]"
             @click="onNanoAODFilterUpdate(nanoaodPair[0])"
             :class="nanoaodPair[0] == nanoaodVersionFilter ? 'bold-text' : ''">{{nanoaodPair[1]}}</a>
        </template>
      </div>
      | 
      <div class="ml-1 mr-1" style="display: inline-block">
        Download Table:
        <a title="Comma-separated values file" class="ml-1 mr-1" @click="downloadExcelFile('csv')">CSV</a>
        <a title="Microsoft Office Excel file" class="ml-1 mr-1" @click="downloadExcelFile('xls')">XLS</a>
      </div>
      |
      <div class="ml-1 mr-1" style="display: inline-block">
        <a class="ml-1 mr-1"
           title="Click here to go to GrASP's github issues"
           target="_blank"
           href="https://github.com/cms-PdmV/GrASP/issues/new/choose">Report a bug or suggest a feature</a>
      </div>
    </div>
    <div v-if="campaign.entries" class="align-center ma-2">
      <b>I am going to add or remove</b>
      <select v-model="selectedPWG" class="ml-2 mr-2">
        <option disabled selected value=''></option>
        <option v-for="pwg in allPWGs" :key="pwg" :value="pwg">{{pwg}}</option>
      </select>
      <b>physics working group as interested PWG in samples</b>
    </div>
    <table v-if="campaign.entries">
      <tr>
        <th>Short Name<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.short_name" @input="applyFilters()"></th>
        <th>Dataset Name<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.dataset" @input="applyFilters()"></th>
        <th>Root Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.root_request" @input="applyFilters()"></th>
        <th>MiniAOD Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.miniaod" @input="applyFilters()"></th>
        <th>NanoAOD Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.nanoaod" @input="applyFilters()"></th>
        <th>Chained Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.chained_request" @input="applyFilters()"></th>
        <th>Interested PWGs</th>
        <!-- <th>Notes</th> -->
      </tr>
      <tr v-for="entry in entries" :key="entry.dataset + entry.uid">
        <td v-if="entry.rowspan.short_name > 0" :rowspan="entry.rowspan.short_name">{{entry.short_name}}</td>
        <td class="dataset-column" v-if="entry.rowspan.dataset > 0" :rowspan="entry.rowspan.dataset">
          <a :href="'https://cms-pdmv.cern.ch/mcm/requests?dataset_name=' + entry.dataset + '&member_of_campaign=' + campaign.name" target="_blank">{{entry.dataset}}</a>
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
            <template v-if="entry.root_request_status === 'submitted'">
              <br>
              <small>Priority: {{entry.root_request_priority}}</small>
            </template>
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
              <div class="mini-nano-version">{{entry.miniaod_version}}</div>
              <br>
              <small>Events: {{entry.miniaodEventsNice}}</small>
              <template v-if="entry.miniaod_status === 'submitted'">
                <br>
                <small>Priority: {{entry.miniaod_priority}}</small>
              </template>
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
              <div class="mini-nano-version">{{entry.nanoaod_version}}</div>
              <br>
              <small>Events: {{entry.nanoaodEventsNice}}</small>
              <template v-if="entry.nanoaod_status === 'submitted'">
                <br>
                <small>Priority: {{entry.nanoaod_priority}}</small>
              </template>
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
        <td class="align-center">
          {{entry.interested_pwgs}}
          <template v-if="selectedPWG && role('user')">
            <br>
            <span class="add-pwg-link" v-if="!entry.interested_pwgs.includes(selectedPWG)" @click="addPWGToEntryAction(selectedPWG, entry)">Add {{selectedPWG}}</span>
            <span class="remove-pwg-link" v-if="entry.interested_pwgs.includes(selectedPWG)" @click="removePWGFromEntryAction(selectedPWG, entry)">Remove {{selectedPWG}}</span>
          </template>
        </td>
      </tr>
    </table>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import ExcelJS from 'exceljs'

export default {
  name: 'existing',
  mixins: [
    utilsMixin,
    roleMixin
  ],
  data () {
    return {
      interestedPWG: undefined,
      selectedPWG: undefined,
      allPWGs: ['B2G', 'BPH', 'BTV', 'EGM', 'EXO', 'FSQ', 'HCA',
                'HGC', 'HIG', 'HIN', 'JME', 'L1T', 'LUM', 'MUO',
                'PPS', 'SMP', 'SUS', 'TAU', 'TOP', 'TRK', 'TSG'],
      campaign: {},
      newEntry: {},
      eventFilterOptions: [[0, 'All'], [5e6, '5M+'], [10e6, '10M+'], [20e6, '20M+'], [50e6, '50M+']],
      eventsFilter: 0,
      miniaodVersionFilterOptions: [['', 'All'], ['MiniAODv1', 'MiniAODv1'], ['MiniAODv2', 'MiniAODv2']],
      miniaodVersionFilter: '',
      nonoaodVersionFilterOptions: [['', 'All'], ['NanoAODv7', 'NanoAODv7'], ['NanoAODv8', 'NanoAODv8']],
      nanoaodVersionFilter: '',
      entries: [], // Filtered entries,
      search: {
        short_name: undefined,
        dataset: undefined,
        root_request: undefined,
        miniaod: undefined,
        nanoaod: undefined,
        chained_request: undefined,
      },
      undoStack: [],
      redoStack: [],
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    let campaignName = query.name;
    if (query.pwg && query.pwg.length) {
      this.interestedPWG = query.pwg.toUpperCase();
    }
    if (query.short_name && query.short_name.length) {
      this.search.short_name = query.short_name.trim();
    }
    if (query.dataset && query.dataset.length) {
      this.search.dataset = query.dataset.trim();
    }
    if (query.root_request && query.root_request.length) {
      this.search.root_request = query.root_request.trim();
    }
    if (query.miniaod && query.miniaod.length) {
      this.search.miniaod = query.miniaod.trim();
    }
    if (query.nanoaod && query.nanoaod.length) {
      this.search.nanoaod = query.nanoaod.trim();
    }
    if (query.chained_request && query.chained_request.length) {
      this.search.chained_request = query.chained_request.trim();
    }
    if (query.events && query.events.length) {
      this.eventsFilter = parseInt(query.events);
    }
    if (query.miniaod_version && query.miniaod_version.length) {
      this.miniaodVersionFilter = query.miniaod_version;
    }
    if (query.nanoaod_version && query.nanoaod_version.length) {
      this.nanoaodVersionFilter = query.nanoaod_version;
    }
    this.fetchCampaign(campaignName);
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
        alert(error.response.data.message);
      });
    },
    processEntry: function(entry) {
      // Add or set to default some attributes
      // and calculate number with SI suffix
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
    fetchCampaign: function(campaignName) {
      let component = this;
      let url = 'api/existing/get/' + campaignName; 
      if (this.interestedPWG) {
        url += '/' + this.interestedPWG;
      }
      axios.get(url).then(response => {
        let campaign = response.data.response;
        campaign.entries.forEach(element => {
          component.processEntry(element);
        });
        component.mergeCells(campaign.entries, ['short_name', 'dataset', 'root_request', 'miniaod'])
        component.$set(component, 'campaign', campaign);
        component.applyFilters();
      }).catch(error => {
        alert(error.response.data.message);
      });
    },
    addPWGToEntryAction: function(pwg, entry) {
      const component = this;
      component.addPWGToEntry(pwg, entry, function(deletedEntry) {
        component.undoStack.push({'action': 'add', 'entry': entry, 'pwg': pwg});
      });
    },
    addPWGToEntry: function(pwg, entry, onSuccess) {
      const component = this;
      entry.interested_pwgs = (this.cleanSplit(entry.interested_pwgs, ',').concat([pwg])).sort().join(',');
      component.updateEntry(entry);
      if (onSuccess) {
        onSuccess(entry);
      }  
    },
    removePWGFromEntryAction: function(pwg, entry) {
      const component = this;
      component.removePWGFromEntry(pwg, entry, function(deletedEntry) {
        component.undoStack.push({'action': 'remove', 'entry': entry, 'pwg': pwg});
      });
    },
    removePWGFromEntry: function(pwg, entry, onSuccess) {
      const component = this;
      entry.interested_pwgs = (this.cleanSplit(entry.interested_pwgs, ',').filter(function(p) { return p !== pwg})).join(',');
      component.updateEntry(entry);
      if (onSuccess) {
        onSuccess(entry);
      }
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
    onMiniAODFilterUpdate: function(miniaod) {
      this.miniaodVersionFilter = miniaod;
      this.applyFilters();
    },
    onNanoAODFilterUpdate: function(nanoaod) {
      this.nanoaodVersionFilter = nanoaod;
      this.applyFilters();
    },
    applyFilters: function() {
      let query = Object.assign({}, this.$route.query);
      let filteredEntries = this.campaign.entries;
      if (this.eventsFilter != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.root_request_total_events >= this.eventsFilter);
        query['events'] = this.eventsFilter;
      } else {
        if ('events' in query) {
          delete query['events'];
        }
      }
      if (this.miniaodVersionFilter.length != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.miniaod_version == this.miniaodVersionFilter);
        query['miniaod_version'] = this.miniaodVersionFilter;
      } else {
        if ('miniaod_version' in query) {
          delete query['miniaod_version'];
        }
      }
      if (this.nanoaodVersionFilter.length != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.nanoaod_version == this.nanoaodVersionFilter);
        query['nanoaod_version'] = this.nanoaodVersionFilter;
      } else {
        if ('nanoaod_version' in query) {
          delete query['nanoaod_version'];
        }
      }
      for (let attribute in this.search) {
        if (this.search[attribute]) {
          const pattern = this.search[attribute].replace(/\.\*/g, '*').replace(/ /g, '*').replace(/\*/g, '.*');
          const regex = RegExp(pattern, 'i'); // 'i' for case insensitivity
          filteredEntries = filteredEntries.filter(entry => entry[attribute] != '' && regex.test(entry[attribute]));
          // Update query parameters
          query[attribute] = this.search[attribute];
        } else {
          if (attribute in query) {
            delete query[attribute];
          }
        }
      }
      this.entries = filteredEntries;
      this.mergeCells(this.entries, ['short_name', 'dataset', 'root_request', 'miniaod']);
      this.$router.replace({query: query}).catch(() => {});
    },
    downloadExcelFile: function(outputFormat) {
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Sheet');
      worksheet.headerRow = true;
      worksheet.columns = [
        { header: 'Short Name', key: 'short_name'},
        { header: 'Dataset', key: 'dataset'},
        { header: 'Root request', key: 'root_request'},
        { header: 'Root request status', key: 'root_request_status'},
        { header: 'Root request priority', key: 'root_request_priority'},
        { header: 'Root request done events', key: 'root_request_done_events'},
        { header: 'Root request total events', key: 'root_request_total_events'},
        { header: 'Root request output', key: 'root_request_output'},
        { header: 'MiniAOD status', key: 'miniaod_status'},
        { header: 'MiniAOD priority', key: 'miniaod_priority'},
        { header: 'MiniAOD done events', key: 'miniaod_done_events'},
        { header: 'MiniAOD total events', key: 'miniaod_total_events'},
        { header: 'MiniAOD output', key: 'miniaod_output'},
        { header: 'NanoAOD status', key: 'nanoaod_status'},
        { header: 'NanoAOD priority', key: 'nanoaod_priority'},
        { header: 'NanoAOD done events', key: 'nanoaod_done_events'},
        { header: 'NanoAOD total events', key: 'nanoaod_total_events'},
        { header: 'NanoAOD output', key: 'nanoaod_output'},
        { header: 'Chained request', key: 'chained_request'},
        { header: 'Interested PWGs', key: 'interested_pwgs'},
      ];

      for (let entry of this.entries) {
        worksheet.addRow({'short_name': entry.short_name,
                          'dataset': entry.dataset,
                          'root_request': entry.root_request,
                          'root_request_status': entry.root_request_status,
                          'root_request_priority': entry.root_request_priority,
                          'root_request_done_events': entry.root_request_done_events,
                          'root_request_total_events': entry.root_request_total_events,
                          'root_request_output': entry.root_request_output,
                          'miniaod_status': entry.miniaod_status,
                          'miniaod_priority': entry.miniaod_priority,
                          'miniaod_done_events': entry.miniaod_done_events,
                          'miniaod_total_events': entry.miniaod_total_events,
                          'miniaod_output': entry.miniaod_output,
                          'nanoaod_status': entry.nanoaod_status,
                          'nanoaod_priority': entry.nanoaod_priority,
                          'nanoaod_done_events': entry.nanoaod_done_events,
                          'nanoaod_total_events': entry.nanoaod_total_events,
                          'nanoaod_output': entry.nanoaod_output,
                          'chained_request': entry.chained_request,
                          'interested_pwgs': entry.interested_pwgs,
                          });
      }
      let fileName = this.campaign.name.replace(/\*/g, 'x');
      if (this.interestedPWG) {
        fileName += '_' + this.interestedPWG;
      }
      if (outputFormat == 'xls') {
        workbook.xlsx.writeBuffer().then(function (data) {
          const blob = new Blob([data], { type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' });
          const url = window.URL.createObjectURL(blob);
          const anchor = document.createElement('a');
          anchor.href = url;
          anchor.download = fileName + '.xls';
          anchor.click();
          window.URL.revokeObjectURL(url);
        });
      } else if (outputFormat == 'csv') {
        workbook.csv.writeBuffer().then(function (data) {
          const blob = new Blob([data], { type: 'text/csv' });
          const url = window.URL.createObjectURL(blob);
          const anchor = document.createElement('a');
          anchor.href = url;
          anchor.download = fileName + '.csv';
          anchor.click();
          window.URL.revokeObjectURL(url);
        });
      }
    },
    undoEvent: function() {
      if (!this.undoStack.length){
        return;
      }
      const component = this;
      let action = this.undoStack.pop()
      if (action.action == 'add') {
        // Save before edit copy
        let entryCopy = Object.assign(action.entry, action.entry);
        let pwgCopy = action.pwg;
        component.removePWGFromEntry(pwgCopy, entryCopy, function(updatedEntry) {
          component.redoStack.push({'action': 'remove', 'entry': entryCopy, 'pwg': pwgCopy});
        });
      } else if (action.action == 'remove') {
        // Save before edit copy
        let entryCopy = Object.assign(action.entry, action.entry);
        let pwgCopy = action.pwg;
        component.addPWGToEntry(pwgCopy, entryCopy, function(updatedEntry) {
          component.redoStack.push({'action': 'add', 'entry': entryCopy, 'pwg': pwgCopy});
        });
      }
    },
    redoEvent: function() {
      if (!this.redoStack.length){
        return;
      }
      const component = this;
      let action = this.redoStack.pop()
      if (action.action == 'remove') {
        // Save before edit copy
        let entryCopy = Object.assign(action.entry, action.entry);
        let pwgCopy = action.pwg;
        component.addPWGToEntry(pwgCopy, entryCopy, function(updatedEntry) {
          component.undoStack.push({'action': 'add', 'entry': entryCopy, 'pwg': pwgCopy});
        });
      } else if (action.action == 'add') {
        // Save before edit copy
        let entryCopy = Object.assign(action.entry, action.entry);
        let pwgCopy = action.pwg;
        component.removePWGFromEntry(pwgCopy, entryCopy, function(updatedEntry) {
          component.undoStack.push({'action': 'remove', 'entry': entryCopy, 'pwg': pwgCopy});
        });
      } 
    }
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

select {
  appearance: auto;
  border: 1px solid black;
  background: white;
}

.add-pwg-link, .remove-pwg-link {
  text-decoration: underline;
  cursor: pointer;
}

.add-pwg-link {
  color: green;
}

.remove-pwg-link {
  color: red;
}

.dataset-column {
  max-width: 285px;
  white-space: normal;
  line-break: anywhere;
}

.bold-text {
  font-weight: 900;
}

.mini-nano-version {
  float: right;
  margin-left: 8px;
}

</style>

