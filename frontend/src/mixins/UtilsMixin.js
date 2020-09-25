export const utilsMixin = {

  methods: {
    listLength(list) {
      if (!list) {
        return 0;
      }
      if (typeof(list) === "string") {
        return list.split('\n').filter(Boolean).length;
      }
      return list.length;
    },
    makeCopy(obj) {
      return JSON.parse(JSON.stringify(obj));
    },
    makeDASLink(dataset) {
      return 'https://cmsweb.cern.ch/das/request?view=list&limit=50&instance=prod%2Fglobal&input=dataset%3D' + dataset;
    },
    cleanSplit(str) {
      if (!str || !str.length) {
        return [];
      }
      return str.replace(/,/g, '\n').split('\n').map(function(s) { return s.trim() }).filter(Boolean);
    },
    getError(response) {
      if (response.response && response.response.data.message) {
        return response.response.data.message;
      }
      return ('Error message could not be found in response, most likely SSO cookie has expired. ' +
              'Try clicking <a href="/grasp" target="blank">here</a>. ' +
              'This will open GrASP homepage in a new tab and hopefully refresh your SSO cookie. ' +
              'You can then close the newly opened tab, dismiss this alert and try performing same action again.');
    },
  }
}
