import axios from 'axios'

export const roleMixin = {

  data: () => ({
    userInfo: undefined,
    fetched: false,
  }),
  created () {
    if (!this.fetched) {
      this.fetched = true;
      this.fetchUserInfo();
    }
  },
  methods: {
    fetchUserInfo () {
      let component = this;
      axios.get('api/system/user_info').then(response => {
        component.userInfo = response.data.response;
      });
    },
    role (roleName) {
      if (!this.userInfo) {
        return false;
      }

      if (roleName == 'user') {
        return true
      } else if (roleName == 'generator_contact') {
        return this.userInfo.role_index >= 1;
      } else if (roleName == 'generator_convener') {
        return this.userInfo.role_index >= 2;
      } else if (roleName == 'production_manager') {
        return this.userInfo.role_index >= 3;
      } else if (roleName == 'administrator') {
        return this.userInfo.role_index >= 4;
      }
      return false;
    },
    getUserInfo () {
      return this.userInfo;
    }
  }
}