<template>
  <div>
    <span style="padding-left: 30px"> You can start creating your custom table here by checking the UL campaigns you're following: </span>
  <div class="form-class" style="text-align: center">
    <span class="input-class"><label for="RunIISummer19UL16*GEN">RunIISummer19UL16*GEN</label>
    <input type="checkbox" id="RunIISummer19UL16*GEN" value="RunIISummer19UL16*GEN" v-model="campaigns"></span>
    <span class="input-class"><label for="RunIISummer19UL17*GEN">RunIISummer19UL17*GEN</label>
    <input  type="checkbox" id="RunIISummer19UL17*GEN" value="RunIISummer19UL17*GEN" v-model="campaigns"></span>
    <span class="input-class"><label for="RunIISummer19UL18*GEN">RunIISummer19UL18*GEN</label>
    <input  type="checkbox" id="RunIISummer19UL18*GEN" value="RunIISummer19UL18*GEN" v-model="campaigns"></span>
    <span class="input-class"><label  for="RunIISummer20UL16*GEN">RunIISummer20UL16*GEN</label>
    <input  type="checkbox" id="RunIISummer20UL16*GEN" value="RunIISummer20UL16*GEN" v-model="campaigns"></span>
    <span class="input-class"><label for="RunIISummer20UL17*GEN">RunIISummer20UL17*GEN</label>
    <input type="checkbox" id="RunIISummer20UL17*GEN" value="RunIISummer20UL17*GEN" v-model="campaigns"></span>
    <span class="input-class"><label for="RunIISummer20UL18*GEN">RunIISummer20UL18*GEN</label>
    <input type="checkbox" id="RunIISummer20UL18*GEN" value="RunIISummer20UL18*GEN" v-model="campaigns"></span>
  </div>
  <div>
    <span style="padding-left: 30px"><label for="datasetnames">Please enter the dataset names you want to follow in your table separated by a | below with no spaces: </label>
    <input style="text-align: center" v-model="datasetnames" v-on:input="generateURL" id="datasetnames" placeholder="TTToHadronic_|ST_t-channel_top_4f_"></span>
    
    <p style="padding-left: 30px">Your custom table is here: <a v-bind:href=url> {{url}}</a> </p>    
  </div>
  </div>
</template>

<script>

export default {
  name: 'CustomTableForm',
  data () {
    return {
    campaigns: [],
    datasetnames: '',
    url: 'https://cms-pdmv.cern.ch/grasp/'
    }
  },
  created () {
  },
  methods: {
      generateURL: function() {
          const campaign_holder = this.campaigns
          let url = 'https://cms-pdmv.cern.ch/grasp/existing?name=' + campaign_holder.join(',') + '&dataset=' + this.datasetnames 
          this.url = url
      }
  }
}
</script>
<style scoped>
    .form-class {
        display: flex;
        flex-flow: row wrap;

        /* Then we define how is distributed the remaining space */
        justify-content: space-around;
    }
    .input-class {
        flex: 1 0 15%;
    }
</style>