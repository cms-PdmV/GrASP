<template>
  <div>
    <h1 class="page-title"><span class="font-weight-light">Creating</span> new user tag</h1>
    <table>
      <tr>
        <td>Tag</td>
        <td><input type="text" v-model="name"></td>
      </tr>
    </table>
    <div style="text-align: center;">
      <b>Note:</b> GrASP synchronizes with McM every 8 hours, so it might <b>take up to 8 hours</b> for requests to appear in GrASP
    </div>
    <div style="text-align: center;">
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()">Save</v-btn>
    </div>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'tag_create',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      name: undefined,
    }
  },
  methods: {
    save: function() {
      const component = this;
      axios.put('api/tags/create', {'name': this.name}).then(() => {
        window.location = 'samples?tag=' + component.name;
      }).catch(error => {
        alert(error.response.data.message);
      });
    },
  }
}
</script>

<style scoped>

input {
  min-width: 200px;
}

</style>
