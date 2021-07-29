<template>
  <div>
    <span style="padding-left: 30px"> You can start creating your custom table here by checking the UL campaigns you're following: </span>
  <div class="form-class" style="text-align: center">
    <span class="input-class"  v-for="campaign in existingCampaigns" :key="campaign"><label for="campaign.name">{{campaign.name}}</label>
    <input type="checkbox" v-on:change="generateURL" v-bind:id="campaign.name" v-bind:value="campaign.name" v-model="campaigns"></span>
  </div>
  <div class="form-class-text">
    <span style="padding-left: 30px"><label for="datasetnames">Please enter the dataset names you want to follow in your table separated by a | below with no spaces: </label>
    <input style="text-align: center; color: blue;" v-model="datasetnames" v-on:input="generateURL" id="datasetnames" placeholder="TTToHadronic_|ST_t-channel_top_4f_"></span>
    
    <p style="padding-left: 30px">Your custom table is here: <a v-bind:href=url> {{url}}</a> </p>    
  </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'CustomTableForm',
  data () {
    return {
    campaigns: [],
    existingCampaigns: [],
    datasetnames: '',
    url: 'https://cms-pdmv.cern.ch/grasp/'
    }
  },
  created () {
    this.fetchObjectsInfo();
  },
  methods: {
      generateURL: function() {
          const campaign_holder = this.campaigns
          let url = 'https://cms-pdmv.cern.ch/grasp/existing?name=' + campaign_holder.join(',') + '&dataset=' + this.datasetnames 
          this.url = url
      },
      fetchObjectsInfo () {
      let component = this;
      axios.get('api/existing/get_all').then(response => {
        component.existingCampaigns = response.data.response;
      });
    },
  }
}
</script>
<style scoped>
    .form-class {
        display: flex;
        flex-flow: row wrap;

        /* Then we define how is distributed the remaining space */
        justify-content: space-around;
        background-color: lightgray;
        border-style: solid;
        margin-left: 20px;
        margin-right: 20px;
    }
    .form-class-text {

        background-color: lightgray;
        border-style: solid;
        border-width: thin;
        margin-left: 20px;
        margin-right: 20px;
    }
    .input-class {
        flex: 1 0 15%;
    }
</style>