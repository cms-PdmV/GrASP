import axios from 'axios'

export const roleMixin = {

  data: () => ({
    userInfo: undefined
  }),
  created () {
    this.fetchUserInfo();
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
      } else if (roleName == 'manager') {
        return this.userInfo.role_index >= 1;
      } else if (roleName == 'administrator') {
        return this.userInfo.role_index >= 2;
      }
    },
    getUserInfo () {
      return this.userInfo;
    }
  }
}