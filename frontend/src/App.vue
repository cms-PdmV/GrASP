<template>
  <v-app>
    <v-app-bar app>
      <a href="" class="no-hover">
        <v-toolbar-title class="headline">
          <span>Gr</span>
          <span class="font-weight-light">ASP</span>
        </v-toolbar-title>
      </a>
      <v-spacer></v-spacer>
      <div v-if="userInfo">
        <span :title="'Username: ' + userInfo.username + '\nRole: ' + userInfo.role"><small>Logged in as</small> {{userInfo.name}} </span>
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
      if (this.role('administrator')) {
        return 'static/admin_star.png';
      }
      if (this.role('user')) {
        return 'static/star.png';
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

.admin-star {
  width: 16px;
  height: 16px;
}

</style>

<style>

.page-title {
  text-align: center;
  margin: 8px 16px;
}

a {
  text-decoration: none;
  transition: color 0.3s;
}

a:hover {
  text-decoration: underline;
}

a.no-hover:hover {
  text-decoration: none;
}

/* Table */
td, th {
  border: 1px #aaa solid;
  padding: 2px 4px;
  font-size: 0.9em;
}

th {
  text-align: center;
  background: #eee;
}

tr {
  height: 30px;
  background: white;
}

table.highlight-on-hover > tr:hover {
  background: #eee !important;
}

table {
  margin-left: auto;
  margin-right: auto;
  margin-bottom: 40px;
  border-collapse: collapse;
}

input {
  border: 1px solid rgba(0, 0, 0, 0.87) !important;
  background: white !important;
  color: rgba(0, 0, 0, 0.87);
  width: 100%;
  padding: 0 4px;
}

td > input[type="checkbox"] {
  margin: auto;
  width: auto;
}

td.hidden-cell {
  visibility: hidden;
  border: 0;
}

/* Convenience */
.align-center {
  text-align: center;
}

.align-left {
  text-align: left;
}

.align-right {
  text-align: right;
}

.red-text {
  color: red;
}

.pointer {
  cursor: pointer;
}

.header-search {
  min-width: 0;
  width: 100%;
  background: white;
  border: 1px solid black;
  font-weight: normal;
  margin-left: -4px;
  margin-right: -4px;
}

.v-app-bar--is-scrolled {
  height: 38px !important;
}

.v-app-bar--is-scrolled > div {
  height: 100% !important;
}

footer {
  padding: 0 12px;
  height: 52px;
  left: 0px;
  right: 0px;
  bottom: 0px;
  position: fixed;
  background: var(--v-background-base) !important;
  box-shadow: 0px -2px 4px -1px rgba(0, 0, 0, 0.2), 0px -4px 5px 0px rgba(0, 0, 0, 0.14), 0px -1px 10px 0px rgba(0, 0, 0, 0.12);
  z-index: 100;
}

footer > a,
footer > span {
  margin-left: 4px;
  line-height: 52px;
  text-decoration: underline;
}

</style>
