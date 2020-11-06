export const utilsMixin = {

  methods: {
    listLength(list) {
      if (!list) {
        return 0;
      }
      if (typeof(list) === 'string') {
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
    suffixNumber(number) {
      if (number === undefined || number === '' || number == null) {
        return '';
      }
      let stripNumber = '';
      let suffix = '';
      let multiplier = 1.0;
      if (number >= 1e9) {
        suffix = 'G';
        multiplier = 1e7;
      } else if (number >= 1e6) {
        suffix = 'M';
        multiplier = 1e4;
      } else if (number >= 1e3) {
        suffix = 'k';
        multiplier = 10;
      } else {
        return number.toString();
      }
      stripNumber = (Math.round(1.0 * number / multiplier) / 100.0).toFixed(2).toString();
      stripNumber = stripNumber.replace(/0+$/, '').replace(/\.$/, '');
      return stripNumber + suffix;
    },
    getRandomInt(max) {
      return Math.floor(Math.random() * Math.floor(max));
    },
  }
}
