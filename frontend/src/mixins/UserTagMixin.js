import axios from 'axios'

export const userTagMixin = {

  data: () => ({
    userTags: []
  }),
  created () {
    this.fetchUserTag();
  },
  methods: {
    fetchUserTag () {
        let component = this;
        axios.get('api/user_tag/get_all').then(response => {
          component.userTags = response.data.response;
        });
      }
  }
}