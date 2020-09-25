<template>
  <v-app>
    <v-app-bar app>
      <a href="" class="no-decoration">
        <v-toolbar-title class="headline">
          <span>Gr</span>
          <span class="font-weight-light">ASP</span>
        </v-toolbar-title>
      </a>
      <v-spacer></v-spacer>
      <div v-if="userInfo">
        <span :title="'Username: ' + userInfo.username + '\nRole: ' + userInfo.role"><small>Logged in as</small> {{userInfo.fullname}} </span>
        <img class="admin-star" :title="'User role: ' + userInfo.role" :src="userRolePicture"/>
      </div>
    </v-app-bar>
    <v-main class="content-container">
      <router-view/>
    </v-main>
  </v-app>
</template>

<script>

import { roleMixin } from './mixins/UserRoleMixin.js'

export default {
  name: 'App',

  mixins: [
    roleMixin
  ],
  computed: {
    userRolePicture: function() {
      if (this.userInfo.role_index == 1) {
        return 'static/star.png';
      }
      if (this.userInfo.role_index == 2) {
        return 'static/admin_star.png';
      }
      return 'static/invisible.png';
    }
  }
};
</script>

<style scoped>

header {
  background: var(--v-background-base) !important;
}

.content-container {
  background: var(--v-backBackground-base);
}

.headline {
  color: rgba(0, 0, 0, 0.87) !important;
}

a.no-decoration {
  text-decoration: none;
}

.admin-star {
  width: 16px;
  height: 16px;
}

</style>

<style>

h1.page-title {
  text-align: center;
  margin: 8px 16px;
}

td, th {
  padding: 6px;
  border: 1px #aaa solid;
}

td {
  position: relative;
}

th {
  text-align: center;
}

table {
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 40px;
  background: white;
  border-collapse: collapse;
}

input {
  border: 1px solid rgba(0, 0, 0, 0.87) !important;
  border-radius: 4px;
  background: #fbfbfb;
  color: rgba(0, 0, 0, 0.87);
  width: 100%;
  padding: 0 4px !important;
}

.page-card input:disabled,
.page-card select:disabled,
.page-card textarea:disabled {
  background: #dadada !important;
  color: rgba(0, 0, 0, 0.65);
  cursor: not-allowed;
}

</style>
