<template>
  <div>
    <div class="form-class-text">
      <h4 style="padding-left: 30px"> You can start creating your custom table here by checking the UL campaigns you're following: </h4>
      <div class="form-class" style="text-align: center">
        <span class="input-class"  v-for="campaign in existingCampaigns" :key="campaign.name"><label for="campaign.name">{{campaign.name}}</label>
        <input type="checkbox" v-on:change="generateURL" v-bind:id="campaign.name" v-bind:value="campaign.name" v-model="campaigns"></span>
      </div>

      <h4 style="padding-left: 30px"><label for="datasetnames">Please enter the dataset names you want to follow in your table separated by a | below with no spaces: </label></h4>
      <input style="text-align: center; border: 1px solid black; width: 60%;background-color: white;" v-model="datasetnames" v-on:input="generateURL" id="datasetnames" placeholder="TTToHadronic_|ST_t-channel_top_4f_">
      <p style="padding-left: 30px">Your custom table is here: <a v-bind:href=url> {{url}}</a> </p>    
    </div>
  
  </div>
</template>

<script>
export default {
  name: 'CustomTableForm',
  props:['existingCampaigns'],
  data () {
    return {
      campaigns: [],
      datasetnames: '',
      url: ''
    }
  },
  created () {
    this.generateURL();
  },
  methods: {
    generateURL: function() {
      const cmpgns = this.campaigns
      let url = location.origin + location.pathname 
      if (cmpgns.length) {
        url += 'existing?name='+ cmpgns.join(',')
      }
      if (this.datasetnames) {
        url += '&dataset=' + this.datasetnames 
      }
      this.url = url
    },
  }
}
</script>
<style scoped>
  .form-class {
    display: flex;
    flex-flow: row wrap;
    justify-content: space-around;
    background-color: #eee;
    border: 2px #aaa solid;
    margin-left: 20px;
    margin-right: 20px;
  }
  .form-class-text {
    text-align: center;
    background-color: #eee;
    border: 1px #aaa solid;
    margin-left: 20px;
    margin-right: 20px;
    margin-bottom: 40px;
  }
  .input-class {
    flex: 1 0 15%;
  }
</style>