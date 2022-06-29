<template>
  <div>
    <h1 v-if="!loading && !fileUpload && (campaign || tags || pwgs)" class="page-title">
      <span class="font-weight-light">Samples </span>
      <template v-if="campaign">
        <span class="font-weight-light">in</span> {{campaign}}
      </template>
      <template v-if="tags">
        <span class="font-weight-light">tagged</span> {{tags}}
      </template>
      <template v-if="pwgs">
        <span class="font-weight-light">where</span> {{pwgs}} <span class="font-weight-light">is interested</span>
      </template>
    </h1>
    <h3 v-if="!loading && !fileUpload && datasetQuery" class="page-title">
      <span class="font-weight-light">Dataset</span> {{datasetQuery}}
    </h3>
    <h1 v-if="!loading && fileUpload" class="page-title">
      File <span class="font-weight-light">upload</span>
    </h1>
    <div class="align-center mt-4" v-if="loading">
      <img :src="'static/loading' + getRandomInt(5) + '.gif'" style="width: 120px; height: 120px;"/>
      <h3 v-if="!drawing">Loading table...</h3>
      <h3 v-if="drawing">Drawing table...</h3>
    </div>
    <div v-if="!loading && (!fileUpload || allEntries.length)" style="margin-top: 10px;" class="align-center">
      <div class="ml-1 mr-1" style="display: inline-block">
        Events:
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
        MiniAOD:
        <template v-for="miniaodPair in miniaodFilterOptions">
          <a :key="miniaodPair[0]"
             class="ml-1 mr-1"
             :title="'Show samples with ' + miniaodPair[0]"
             @click="onMiniAODFilterUpdate(miniaodPair[0])"
             :class="miniaodPair[0] == miniaodFilter ? 'bold-text' : ''">{{miniaodPair[1]}}</a>
        </template>
      </div>
      |
      <div class="ml-1 mr-1" style="display: inline-block">
        NanoAOD:
        <template v-for="nanoaodPair in nanoaodFilterOptions">
          <a :key="nanoaodPair[0]"
             class="ml-1 mr-1"
             :title="'Show samples with ' + nanoaodPair[0]"
             @click="onNanoAODFilterUpdate(nanoaodPair[0])"
             :class="nanoaodPair[0] == nanoaodFilter ? 'bold-text' : ''">{{nanoaodPair[1]}}</a>
        </template>
      </div>
      |
      <div class="ml-1 mr-1" style="display: inline-block">
        Download table:
        <a title="Comma-separated values file" class="ml-1 mr-1" @click="downloadExcelFile('csv')">CSV</a>
        <a title="Microsoft Office Excel file" class="ml-1 mr-1" @click="downloadExcelFile('xls')">XLS</a>
      </div>
    </div>
    <div v-if="!loading && (!fileUpload || allEntries.length)" class="align-center ma-2">
      Add or remove
      <select v-model="selectedPWG" class="ml-1 mr-1" style="padding: 0 4px;">
        <option selected value=''></option>
        <option v-for="pwg in allPWGs" :key="pwg" :value="pwg">{{pwg}}</option>
      </select>
      interested PWG or
      <select v-model="selectedTag" class="ml-1 mr-1" style="padding: 0 4px;">
        <option selected value=''></option>
        <option v-for="tag in allTags" :key="tag" :value="tag">{{tag}}</option>
      </select>
      tag
    </div>
    <table v-if="!loading && (!fileUpload || allEntries.length)">
      <tr>
        <th rowspan="2">Short Name<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.short_name" @input="applyFilters()"></th>
        <th rowspan="2">Dataset Name<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.dataset" @input="applyFilters()"></th>
        <th colspan="3">Root Request</th>
        <th rowspan="2">MiniAOD Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.miniaod" @input="applyFilters()"></th>
        <th rowspan="2">NanoAOD Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.nanoaod" @input="applyFilters()"></th>
        <th rowspan="2">Chained Request<br><input type="text" class="header-search" placeholder="Type to search..." v-model="search.chained_request" @input="applyFilters()"></th>
        <th rowspan="2" style="text-align: center">
          <input type="checkbox" style="width: auto" :checked="selectAllChecked" v-on:change="toggleAllCheckboxes" v-model="selectAllChecked" :indeterminate.prop="selectAllIndeterminate">
        </th>
      </tr>
      <tr>
        <th>Tags</th>
        <th title="Interested PWGs">Int. PWGs</th>
        <th><input type="text" class="header-search" placeholder="Type to search..." v-model="search.root" @input="applyFilters()"></th>
      </tr>
      <tr v-for="entry in entries" :key="entry._id">
        <td v-if="entry.rowspan.short_name > 0" :rowspan="entry.rowspan.short_name">{{entry.short_name}}</td>
        <td class="dataset-column" v-if="entry.rowspan.dataset > 0" :rowspan="entry.rowspan.dataset">
          <a :href="'https://cms-pdmv.cern.ch/mcm/requests?dataset_name=' + entry.dataset" target="_blank">{{entry.dataset}}</a>
        </td>
        <td v-if="entry.rowspan.root > 0" :rowspan="entry.rowspan.root" class="tags-cell">{{entry.tagsNice}}
          <template v-if="selectedTag && role('user')">
            <br>
            <span class="add-pwg-link" v-if="!entry.tags.includes(selectedTag)" @click="addTagToEntries(selectedTag, [entry])">Add {{selectedTag}}</span>
            <span class="remove-pwg-link" v-if="entry.tags.includes(selectedTag)" @click="removeTagFromEntries(selectedTag, [entry])">Remove {{selectedTag}}</span>
          </template>
        </td>
        <td v-if="entry.rowspan.root > 0" :rowspan="entry.rowspan.root" class="tags-cell">{{entry.pwgsNice}}
          <template v-if="selectedPWG && role('user')">
            <br>
            <span class="add-pwg-link" v-if="!entry.pwgs.includes(selectedPWG)" @click="addPWGToEntries(selectedPWG, [entry])">Add {{selectedPWG}}</span>
            <span class="remove-pwg-link" v-if="entry.pwgs.includes(selectedPWG)" @click="removePWGFromEntries(selectedPWG, [entry])">Remove {{selectedPWG}}</span>
          </template>
        </td>
        <td v-if="entry.rowspan.root > 0" :rowspan="entry.rowspan.root" class="progress-cell">
          <div>
            <a :href="'https://cms-pdmv.cern.ch/mcm/requests?prepid=' + entry.root" target="_blank">McM</a>
            <a :href="'https://cms-pdmv.cern.ch/pmp/historical?r=' + entry.root" target="_blank" class="ml-1">pMp</a>
            <template v-if="entry.root_output">
              <a :href="makeDASLink(entry.root_output)" target="_blank" class="ml-1">DAS</a>
            </template>
            <br>
            <small>{{entry.campaign}}</small>
            <br>
            <small>Events: {{entry.rootEventsNice}}</small>
            <template v-if="entry.root_status === 'submitted'">
              <br>
              <small>Priority: {{entry.root_priority}}</small>
            </template>
            <template v-if="entry.root_status !== 'done'">
              <br>
              <small>Status: {{entry.root_status}}</small>
            </template>
            <br>
            <small><i>{{entry.root_processing_string}}</i></small>
          </div>
          <div :class="'progress-background ' + entry.root_status + '-background'"
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
              <template v-if="entry.miniaod_status !== 'done'">
                <br>
                <small>Status: {{entry.miniaod_status}}</small>
              </template>
              <br>
              <small><i>{{entry.miniaod_processing_string}}</i></small>
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
              <template v-if="entry.nanoaod_status !== 'done'">
                <br>
                <small>Status: {{entry.nanoaod_status}}</small>
              </template>
              <br>
              <small><i>{{entry.nanoaod_processing_string}}</i></small>
            </div>
            <div :class="'progress-background ' + entry.nanoaod_status + '-background'"
                 :style="'width: ' + entry.nanoaodPercentage + '%;'">
            </div>
          </template>
        </td>
        <td>
          <a :href="'https://cms-pdmv.cern.ch/mcm/chained_requests?prepid=' + entry.chained_request" target="_blank">{{entry.chain_tag}}</a>
        </td>
        <td style="min-width: 30px; text-align: center">
          <input type="checkbox" :checked="entry.checked" v-on:change="toggleOneCheckbox" v-model="entry.checked">
        </td>
      </tr>
    </table>
    <div v-if="entries.length" class="entries-count">
      <small>Rows: {{entries.length}}/{{allEntries.length}}</small>
    </div>

    <form v-show="!loading && fileUpload && !allEntries.length"
          class="file-upload"
          enctype="multipart/form-data"
          @click="openFileChooseDialog()"
          ref="file-upload-form">
      <input style="display: none" type="file" ref="file-upload-input" />
      <v-icon style="font-size: 80px">mdi-file-upload-outline</v-icon>
      <br>
      <b>Click here</b> to choose a file <span v-if="dragDropSupported">or drag and drop it in dashed area</span>
      <br>
      <div style="line-height: 80%; margin-top: 8px;">
        <small>Only plain text files are supported, where contents are dataset names, one per line</small>
      </div>
    </form>

    <footer v-if="selectedCount > 0">
      Selected items ({{selectedCount}}) actions:
      <template v-if="role('user')">
        <span v-if="selectedTag" class="add-pwg-link" @click="addTagToSelectedEntries(selectedTag)">Add {{selectedTag}}</span>
        <span v-if="selectedTag" class="remove-pwg-link" @click="removeTagFromSelectedEntries(selectedTag)">Remove {{selectedTag}}</span>
        <span v-if="selectedPWG" class="add-pwg-link" @click="addPWGToSelectedEntries(selectedPWG)">Add {{selectedPWG}}</span>
        <span v-if="selectedPWG" class="remove-pwg-link" @click="removePWGFromSelectedEntries(selectedPWG)">Remove {{selectedPWG}}</span>
      </template>
      <span style="color: var(--v-anchor-base); cursor: pointer" @click="openPmpSelectedEntries()">pMp Historical</span>
    </footer>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'
import { roleMixin } from '../mixins/UserRoleMixin.js'
import ExcelJS from 'exceljs'

export default {
  name: 'samples',
  mixins: [
    utilsMixin,
    roleMixin,
  ],
  data () {
    return {
      loading: true,
      drawing: false,
      campaign: undefined,
      pwgs: undefined,
      tags: undefined,
      datasetQuery: undefined,
      fileUpload: false,
      dragDropSupported: false,
      selectedPWG: undefined,
      selectedTag: undefined,
      allPWGs: ['B2G', 'BPH', 'BTV', 'EGM', 'EXO', 'FSQ', 'GEN', 'HCA',
                'HGC', 'HIG', 'HIN', 'JME', 'L1T', 'LUM', 'MUO',
                'PPS', 'SMP', 'SUS', 'TAU', 'TOP', 'TRK', 'TSG'],
      allTags: [],
      eventFilterOptions: [[0, 'All'], [5e6, '5M+'], [10e6, '10M+'], [20e6, '20M+'], [50e6, '50M+']],
      eventsFilter: 0,
      miniaodFilterOptions: [],
      miniaodFilter: '',
      nanoaodFilterOptions: [],
      nanoaodFilter: '',
      allEntries: [], // All fetched entries
      entries: [], // Filtered entries,
      search: {
        short_name: undefined,
        dataset: undefined,
        root: undefined,
        miniaod: undefined,
        nanoaod: undefined,
        chained_request: undefined,
      },
      selectAllChecked: false,
      selectAllIndeterminate: false,
      selectedCount: 0,
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    if (query.campaign && query.campaign.length) {
      this.campaign = query.campaign.trim();
    }
    if (query.pwgs && query.pwgs.length) {
      this.pwgs = query.pwgs.toUpperCase();
    }
    if (query.tags && query.tags.length) {
      this.tags = query.tags.trim();
    }
    if (query.dataset_query && query.dataset_query.length) {
      this.datasetQuery = query.dataset_query.trim();
    }
    if (query.short_name && query.short_name.length) {
      this.search.short_name = query.short_name.trim();
    }
    if (query.dataset && query.dataset.length) {
      this.search.dataset = query.dataset.trim();
    }
    if (query.root && query.root.length) {
      this.search.root = query.root.trim();
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
      this.miniaodFilter = query.miniaod_version;
    }
    if (query.nanoaod_version && query.nanoaod_version.length) {
      this.nanoaodFilter = query.nanoaod_version;
    }
    if (query.file) {
      this.fileUpload = true;
    }
  },
  mounted() {
    this.fetchTags();
    if (!this.fileUpload) {
      this.fetchEntries(undefined);
    } else {
      this.prepareFileUploadForm();
      this.loading = false;
    }
  },
  methods: {
    fetchEntries: function(file) {
      let query = [];
      if (this.campaign) {
        query.push('campaign=' + this.campaign)
      }
      if (this.tags) {
        query.push('tags=' + this.tags)
      }
      if (this.pwgs) {
        query.push('pwgs=' + this.pwgs)
      }
      if (this.datasetQuery && !file) {
        query.push('dataset=' + this.datasetQuery);
      }
      if (!query.length && !file) {
        this.loading = false;
        return;
      }
      let component = this;
      let url = 'api/samples/get?' + query.join('&');
      let method = undefined;
      this.loading = true;
      if (file) {
        let formData = new FormData();
        formData.append('file', file);
        method = axios.post(url, formData, { headers: {'Content-Type': 'multipart/form-data' }});
      } else {
        method = axios.get(url);
      }
      method.then(response => {
        let entries = response.data.response;
        entries.forEach(element => {
          component.processEntry(element);
        });
        component.miniaodFilterOptions = Array.from(new Set(['', ...entries.map(x => x.miniaod_version).sort()]), x => [x, x == '' ? 'All' : x]);
        component.nanoaodFilterOptions = Array.from(new Set(['', ...entries.map(x => x.nanoaod_version).sort()]), x => [x, x == '' ? 'All' : x]);
        component.mergeCells(entries, ['short_name', 'dataset', 'root', 'miniaod']);
        component.allEntries = entries;
        component.drawing = true;
        setTimeout(() => {
          component.applyFilters();
          component.loading = false;
          component.drawing = false;
        }, 20);
      }).catch(error => {
        alert(error.response.data.message);
      });
    },
    processEntry: function(entry) {
      // Add or set to default some attributes
      // and calculate number with SI suffix
      entry.rootDoneEventsNice = this.suffixNumber(entry.root_done_events);
      entry.rootTotalEventsNice = this.suffixNumber(entry.root_total_events);
      entry.miniaodDoneEventsNice = this.suffixNumber(entry.miniaod_done_events);
      entry.miniaodTotalEventsNice = this.suffixNumber(entry.miniaod_total_events);
      entry.nanoaodDoneEventsNice = this.suffixNumber(entry.nanoaod_done_events);
      entry.nanoaodTotalEventsNice = this.suffixNumber(entry.nanoaod_total_events);
      if ((entry.root_status == 'submitted' || entry.root_status == 'done') && entry.root_output.length && entry.root_total_events) {
        entry.rootPercentage = entry.root_done_events / entry.root_total_events * 100;
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
      entry.checked = entry.checked !== undefined ? entry.checked : false;
      entry.pwgsNice = entry.pwgs.join(', ');
      entry.tagsNice = entry.tags.join(', ');
    },
    fetchTags: function() {
      const component = this;
      axios.get('api/tags/get_all').then(response => {
        component.allTags = response.data.response;
      });
    },
    openFileChooseDialog: function() {
      let formInput = this.$refs['file-upload-input'];
      formInput.click()
    },
    prepareFileUploadForm: function() {
      let divElement = document.createElement('div');
      this.dragDropSupported = (('draggable' in divElement) || ('ondragstart' in divElement && 'ondrop' in divElement)) && 'FormData' in window && 'FileReader' in window;
      const component = this;
      if (this.dragDropSupported) {
        let form = this.$refs['file-upload-form'];
        const stopPropagation = function(e) {
          e.preventDefault();
          e.stopPropagation();
        }
        const draggingOver = function(e) {
          stopPropagation(e);
          form.classList.add('dragging-over');
        }
        const notDragingOver = function(e) {
          stopPropagation(e);
          form.classList.remove('dragging-over');
        }
        const drop = function(e) {
          notDragingOver(e);
          component.fetchEntries(e.dataTransfer.files[0]);
        }
        form.ondrag = stopPropagation;
        form.ondragstart = stopPropagation;
        form.ondragenter = notDragingOver;
        form.ondragover = draggingOver;
        form.ondragend = notDragingOver;
        form.ondragleave = notDragingOver;
        form.ondrop = drop;
      }

      let formInput = this.$refs['file-upload-input'];
      formInput.onchange = function() {
        component.fetchEntries(formInput.files[0]);
      }
    },
    addPWGToSelectedEntries: function(pwg) {
      this.addPWGToEntries(pwg, this.entries.filter(x => x.checked));
    },
    addPWGToEntries: function(pwg, entries) {
      let entriesToUpdate = [];
      for (let entry of entries) {
        entriesToUpdate.push({'prepid': entry.root, 'action': 'add_pwg', 'value': pwg})
      }
      this.updateEntries(entriesToUpdate);
    },
    removePWGFromSelectedEntries: function(pwg) {
      this.removePWGFromEntries(pwg, this.entries.filter(x => x.checked));
    },
    removePWGFromEntries: function(pwg, entries) {
      let entriesToUpdate = [];
      for (let entry of entries) {
        entriesToUpdate.push({'prepid': entry.root, 'action': 'remove_pwg', 'value': pwg})
      }
      this.updateEntries(entriesToUpdate);
    },
    addTagToSelectedEntries: function(tag) {
      this.addTagToEntries(tag, this.entries.filter(x => x.checked));
    },
    addTagToEntries: function(tag, entries) {
      let entriesToUpdate = [];
      for (let entry of entries) {
        entriesToUpdate.push({'prepid': entry.root, 'action': 'add_tag', 'value': tag})
      }
      this.updateEntries(entriesToUpdate);
    },
    removeTagFromSelectedEntries: function(tag) {
      this.removeTagFromEntries(tag, this.entries.filter(x => x.checked));
    },
    removeTagFromEntries: function(tag, entries) {
      let entriesToUpdate = [];
      for (let entry of entries) {
        entriesToUpdate.push({'prepid': entry.root, 'action': 'remove_tag', 'value': tag})
      }
      this.updateEntries(entriesToUpdate);
    },
    updateEntries: function(entries) {
      let httpRequest = axios.post('api/samples/update', entries, { timeout: 120000 });
      const component = this;
      if (entries.length > 100) {
        this.loading = true;
      }
      httpRequest.then(response => {
        component.loading = false;
        for (let updatedEntry of response.data.response) {
          for (let existingEntry of this.allEntries) {
            if (updatedEntry._id == existingEntry._id) {
              // Update existing entry
              Object.assign(existingEntry, updatedEntry);
              component.processEntry(existingEntry);
              break
            }
          }
        }
      }).catch(error => {
        component.loading = false;
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
    onMiniAODFilterUpdate: function(miniaod) {
      this.miniaodFilter = miniaod;
      this.applyFilters();
    },
    onNanoAODFilterUpdate: function(nanoaod) {
      this.nanoaodFilter = nanoaod;
      this.applyFilters();
    },
    applyFilters: function() {
      let query = Object.assign({}, this.$route.query);
      let filteredEntries = this.allEntries;
      if (this.eventsFilter != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.root_total_events >= this.eventsFilter);
        query['events'] = this.eventsFilter;
      } else {
        if ('events' in query) {
          delete query['events'];
        }
      }
      if (this.miniaodFilter.length != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.miniaod_version == this.miniaodFilter);
        query['miniaod_version'] = this.miniaodFilter;
      } else {
        if ('miniaod_version' in query) {
          delete query['miniaod_version'];
        }
      }
      if (this.nanoaodFilter.length != 0) {
        filteredEntries = filteredEntries.filter(entry => entry.nanoaod_version == this.nanoaodFilter);
        query['nanoaod_version'] = this.nanoaodFilter;
      } else {
        if ('nanoaod_version' in query) {
          delete query['nanoaod_version'];
        }
      }
      for (let attribute in this.search) {
        let pattern = this.search[attribute];
        if (pattern && pattern.length && pattern != '-' && pattern != '!') {
          let negate = false;
          if (pattern[0] == '-' || pattern[0] == '!') {
            negate = true;
            pattern = pattern.substring(1);
          }
          pattern = pattern.replaceAll('.*', '*').replaceAll(' ', '*').replaceAll('*', '.*').replaceAll(',', '|');
          const regex = RegExp(pattern, 'i'); // 'i' for case insensitivity
          const filterFunc = function(entry) {
            const value = entry[attribute];
            if (value == undefined || value == '') {
              // If negating, empty value should be shown
              return negate;
            }
            return regex.test(value) ^ negate;
          }
          filteredEntries = filteredEntries.filter(filterFunc);
          // Update query parameters
          query[attribute] = this.search[attribute].trim();
        } else {
          if (attribute in query) {
            delete query[attribute];
          }
        }
      }
      this.$set(this, 'entries', filteredEntries);
      this.toggleOneCheckbox();
      this.mergeCells(this.entries, ['short_name', 'dataset', 'root', 'miniaod']);
      this.$router.replace({query: query}).catch(() => {});
    },
    downloadExcelFile: function(outputFormat) {
      const workbook = new ExcelJS.Workbook();
      const worksheet = workbook.addWorksheet('Sheet');
      worksheet.headerRow = true;
      worksheet.columns = [
        { header: 'Short Name', key: 'short_name'},
        { header: 'Dataset', key: 'dataset'},
        { header: 'Root request', key: 'root'},
        { header: 'Root request status', key: 'root_status'},
        { header: 'Root request priority', key: 'root_priority'},
        { header: 'Root request done events', key: 'root_done_events'},
        { header: 'Root request total events', key: 'root_total_events'},
        { header: 'Root request output', key: 'root_output'},
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
        { header: 'Interested PWGs', key: 'pwgs'},
        { header: 'Tags', key: 'tags'},
      ];

      for (let entry of this.entries) {
        worksheet.addRow({'short_name': entry.short_name,
                          'dataset': entry.dataset,
                          'root': entry.root,
                          'root_status': entry.root_status,
                          'root_priority': entry.root_priority,
                          'root_done_events': entry.root_done_events,
                          'root_total_events': entry.root_total_events,
                          'root_output': entry.root_output,
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
                          'pwgs': entry.pwgs.join(', '),
                          'tags': entry.tags.join(', '),
                          });
      }
      let fileName = ['GrASP'];
      if (this.campaign) {
        fileName.push(this.campaign);
      }
      if (this.tags) {
        fileName.push(this.tags);
      }
      if (this.pwgs) {
        fileName.push(this.pwgs);
      }
      if (this.datasetQuery) {
        fileName.push(this.datasetQuery);
      }
      fileName = fileName.join('_').replaceAll(',', '_').replace(/[^A-Za-z0-9_-]/g, 'x');
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
    toggleAllCheckboxes: function() {
      this.selectAllIndeterminate = false;
      if (this.selectAllChecked) {
        this.entries.forEach(x => x.checked = true);
        this.selectedCount = this.entries.length;
      } else {
        this.entries.forEach(x => x.checked = false);
        this.selectedCount = 0;
      }
    },
    toggleOneCheckbox: function() {
      if (this.entries.every(x => x.checked)) {
        // If all selected
        this.selectedCount = this.entries.length;
        this.selectAllChecked = this.entries.length > 0;
        this.selectAllIndeterminate = false;
      } else if (this.entries.some(x => x.checked)) {
        // If some are selected
        this.selectedCount = this.entries.filter(x => x.checked).length;
        this.selectAllChecked = false;
        this.selectAllIndeterminate = true;
      } else {
        // If none are selected
        this.selectedCount = 0;
        this.selectAllChecked = false;
        this.selectAllIndeterminate = false;
      }
    },
    openPmpSelectedEntries: function() {
      let prepids = [];
      for (let entry of this.entries.filter(x => x.checked)) {
        let prepid = undefined;
        let status = undefined;
        if (entry.nanoaod) {
          prepid = entry.nanoaod;
          status = entry.nanoaod_status;
        } else if (entry.miniaod) {
          prepid = entry.miniaod;
          status = entry.miniaod_status;
        } else if (entry.root) {
          prepid = entry.root;
          status = entry.root_status;
        }
        if (status == 'submitted' || status == 'done') {
          prepids.push(prepid);
        }
      }
      if (prepids.length) {
        let url = window.location.origin + '/pmp/historical?r=' + prepids.join(',');
        window.open(url, '_blank');
      }
    }
  }
}
</script>

<style scoped>

table {
  margin-bottom: 64px;
}

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
  font-weight: normal;
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
  font-size: 0.8em;
}

td.tags-cell {
  text-align: center;
  max-width: 150px;
  min-height: 50px;
  min-width: 70px;
  overflow: auto;
  white-space: break-spaces;
  word-break: break-word;
}

form.file-upload {
  max-width: 400px;
  margin: auto;
  border: 2px gray dashed;
  border-radius: 40px;
  padding: 50px;
  text-align: center;
  cursor: pointer
}

form.file-upload.dragging-over {
  background-color: #eaeaea;
}

.entries-count {
  text-align: center;
  cursor: default;
  opacity: 0.05;
}

.entries-count:hover {
  opacity: 1;
}

</style>
