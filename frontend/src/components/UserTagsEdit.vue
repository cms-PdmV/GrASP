<template>
  <div>
    <h1 class="page-title" v-if="creatingNew"><span class="font-weight-light">Creating</span> new tag</h1>
    <h1 class="page-title" v-else><span class="font-weight-light">Editing</span> {{tagName}}</h1>
    <table v-if="tag">
      <tr>
        <td>Name</td>
        <td><input type="text" v-model="tag.name"></td>
      </tr>
    </table>
    <div style="text-align: center;">
      <v-btn small class="mr-1 mt-1" color="primary" @click="save()">Save</v-btn>
      <v-btn small class="mr-1 mt-1" color="error" v-if="!creatingNew" @click="deleteTag()">Delete</v-btn>
    </div>
    <v-dialog v-model="dialog.visible"
              max-width="50%">
      <v-card>
        <v-card-title class="headline">
          {{dialog.title}}
        </v-card-title>
        <v-card-text>
          <span v-html="dialog.description"></span>
        </v-card-text>
        <v-card-actions>
          <v-spacer></v-spacer>
          <v-btn small class="mr-1 mb-1" color="primary" v-if="dialog.cancel" @click="dialog.cancel">
            Cancel
          </v-btn>
          <v-btn small class="mr-1 mb-1" color="error" @click="dialog.ok">
            OK
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>

import axios from 'axios'
import { utilsMixin } from '../mixins/UtilsMixin.js'

export default {
  name: 'existing_edit',
  mixins: [
    utilsMixin
  ],
  data () {
    return {
      tagName: undefined,
      tag: undefined,
      creatingNew: true,
      dialog: {
        visible: false,
        title: '',
        description: '',
        cancel: undefined,
        ok: undefined,
      },
    }
  },
  created () {
    let query = Object.assign({}, this.$route.query);
    if (query.name && query.name.length) {
      this.tagName = query.name;
    } else {
      this.tagName = '';
    }
    this.creatingNew = this.tagName.length == 0;
    if (this.creatingNew) {
      this.tag = {'name': ''};
    } else {
      let component = this;
      axios.get('api/user_tag/get/' + this.tagName).then(response => {
        component.tag = response.data.response;
      }).catch(error => {
        alert(error.response.data.message);
      });
    }
  },
  methods: {
    save: function() {
      let tag = this.makeCopy(this.tag);
      let httpRequest;
      if (this.creatingNew) {
        httpRequest = axios.put('api/user_tag/create', tag);
      } else {
        httpRequest = axios.post('api/user_tag/update', tag);
      }
      let component = this;
      httpRequest.then(() => {
        window.location = 'tags?name=' + component.tag.name;
      }).catch(error => {
        alert(error.response.data.message);
      });
    },
    clearDialog: function() {
      this.dialog.visible = false;
      this.dialog.title = '';
      this.dialog.description = '';
      this.dialog.ok = function() {};
      this.dialog.cancel = function() {};
    },
    deleteTag: function() {
      let component = this;
      this.dialog.title = "Delete " + this.tagName + " tag?";
      this.dialog.description = "Are you sure you want to delete " + this.tagName + " and all it's entries from GrASP?";
      this.dialog.ok = function() {
        let tag = component.makeCopy(component.tag);
        axios.delete('api/user_tag/delete', {data: tag}).then(() => {
          component.clearDialog();
          window.location = '';
        }).catch(error => {
          alert(error.response.data.message);
        });
      }
      this.dialog.cancel = this.clearDialog;
      this.dialog.visible = true;
    },
  }
}
</script>

<style scoped>

input {
  min-width: 300px;
}

</style>