<template>
  <div>
    <div style="display: flex; flex-direction: row; flex-wrap: wrap; justify-content: space-evenly;">
      <div v-for="campaign in campaignNames"
           :key="campaign"
           style="white-space: nowrap; margin: 1px 8px; text-align: center">
        <label>
          <input type="checkbox"
                 style="width: auto"
                 :name="campaign"
                 v-model="campaigns[campaign]">&nbsp;{{campaign}}
        </label>
      </div>
    </div>
    <div style="position: relative">
      <input
        type="text"
        v-model="value"
        id="search-input"
        :placeholder="randomPlaceholder"
        @focus="makeFocused(true)"
        @blur="makeFocused(false)"
        v-on:keydown.up.capture.prevent="arrowKey(-1)"
        v-on:keydown.down.capture.prevent="arrowKey(1)"
        v-on:keydown.enter.capture.prevent="enterKey()"
      />
      <v-progress-circular
        :size="18"
        :width="2"
        style="margin: 4px 0; position: absolute; right: 4px"
        color="primary"
        indeterminate
        v-if="suggestionsTimer || loading"
      ></v-progress-circular>
      <div
        class="suggestion-list-wrapper"
        @mouseover="mouseEnteredList(true)"
        @mouseleave="mouseEnteredList(false)"
      >
        <div class="elevation-3 suggestion-list">
          <div
            v-for="(value, index) in items"
            :key="index"
            class="suggestion-item"
            @click="select(value.link)"
            @mouseover="mouseEnteredItem(index)"
            v-bind:class="{ 'suggestion-item-hover': index == selectedIndex }"
          >
            <div style="line-break: anywhere" v-html="highlight(value)"></div>
          </div>
        </div>
      </div>
    </div>
    <small><i>Spaces and asterisks act as wildcards, use comma to specify more than one term</i></small>
  </div>
</template>

<script>
import axios from "axios";
/* component needs to do to be compatible with v-model
   is accept a :value property and emit an @input event
   when the user changes the value.
*/
export default {
  props: ['campaignNames'],
  data() {
    return {
      items: [],
      savedItems: [],
      cache: {},
      isFocused: false,
      value: undefined,
      mouseInside: false,
      suggestionsTimer: undefined,
      suggestionsWait: 600,
      ignoreChange: false,
      selectedIndex: 0,
      loading: false,
      campaigns: {},
    };
  },
  created() {},
  watch: {
    campaignNames() {
      for (let name of this.campaignNames) {
        this.campaigns[name] = true;
      }
    },
    isFocused(focused) {
      if (!focused) {
        this.savedItems = this.items;
        this.items = [];
      } else {
        this.items = this.savedItems;
        this.savedItems = [];
      }
    },
    value(newValue) {
      this.selectedIndex = 0;
      if (!this.isFocused) {
        return;
      }
      if (this.ignoreChange) {
        this.ignoreChange = false;
        return;
      }
      if (!newValue || !newValue.length) {
        this.items = [];
        return;
      }

      if (this.suggestionsTimer) {
        clearTimeout(this.suggestionsTimer);
        this.suggestionsTimer = undefined;
      }
      this.items = [];
      // Trim in case there are spaces around
      newValue = newValue.replace(/[^*A-Za-z0-9-_, ]/g, ' ').replace(/\*+/g, '*').replace(/ +/g, ' ').trim();
      let lastPart = newValue.split(',').pop().replaceAll('*', ' ').trim().replace(/ +/g, '*');
      let lastPartLength = lastPart.replaceAll('*', '').length;
      if (lastPartLength < 3) {
        this.items = [];
        return;
      }
      newValue = newValue.split(',').filter(x => x.replace(/[* ]/g, '').length).map(x => x.trim()).join(',').replace(/\*+/g, '*').replace(/ +/g, ' ');
      let link = newValue.replaceAll(' ', '*').split(',').map(x => `*${x}*`).join(',').replaceAll(' ', '*').replace(/\*+/g, '*');
      if (lastPart in this.cache) {
        this.items = this.cache[lastPart];
        this.items = this.items.map(function (x) {return {'wild': false, 'value': x, 'link': x}});
        if (!this.cache[lastPart].includes(newValue)) {
          this.items.unshift({'wild': true,
                              'value': newValue,
                              'link': link});
        }
        this.suggestionsTimer = undefined;
      } else {
        this.suggestionsTimer = setTimeout(() => {
          const component = this;
          component.suggestionsTimer = undefined;
          component.loading = true;
          axios.get("api/search?q=" + lastPart).then((response) => {
            component.items = response.data.response;
            component.cache[lastPart] = component.items;
            component.items = component.items.map(function (x) {return {'wild': false, 'value': x, 'link': x}});
            if (!response.data.response.includes(newValue)) {
              this.items.unshift({'wild': true,
                                  'value': newValue,
                                  'link': link});
            }
            component.loading = false;
          }).catch(() => {
            component.loading = false;
          });
        }, this.suggestionsWait);
      }
    },
  },
  methods: {
    select(value) {
      this.ignoreChange = true;
      let selectedCampaigns = this.campaignNames.filter(x => this.campaigns[x]).sort().join(',');
      if (!selectedCampaigns.length) {
        alert('No campaigns selected');
        return;
      }
      let url = window.location.origin + "/grasp/samples?dataset_query=" + value + "&campaign=" + selectedCampaigns;
      window.location.href = url;
    },
    makeFocused(focused) {
      if (!this.mouseInside || focused) {
        this.isFocused = focused;
      }
    },
    mouseEnteredList(entered) {
      this.mouseInside = entered;
    },
    mouseEnteredItem(index) {
      this.selectedIndex = index;
    },
    highlight(item) {
      let splitValues = this.value.split(',').filter(Boolean)
      let value = splitValues[splitValues.length - 1].toLowerCase().replace(/\*/g, " ").split(" ").filter(Boolean);
      let highlighted = "";
      let lastIndex = 0;
      let lowerCaseItem = item.value.toLowerCase();
      for (let split of value) {
        let foundIndex = lowerCaseItem.indexOf(split, lastIndex);
        if (foundIndex < 0) {
          continue;
        }
        highlighted += item.value.slice(lastIndex, foundIndex);
        lastIndex += foundIndex - lastIndex;
        let highlightedPiece = item.value.slice(foundIndex, foundIndex + split.length);
        highlighted += '<b style="background: #dadada">' + highlightedPiece + '</b>';
        lastIndex += split.length;
      }
      highlighted += item.value.slice(lastIndex);
      if (item.wild) {
        highlighted = highlighted.replaceAll(',', '" or "');
        highlighted = '<i>All samples with "' + highlighted + '"</i>';
      }
      return highlighted;
    },
    arrowKey(direction) {
      const itemsLength = this.items.length;
      if (!itemsLength) {
        this.selectedIndex = 0;
        return;
      }
      this.selectedIndex =
        (itemsLength + this.selectedIndex + direction) % itemsLength;
    },
    enterKey() {
      if (!this.items.length) {
        return;
      }
      this.select(this.items[this.selectedIndex]);
    },
  },
  computed: {
    randomPlaceholder: function () {
      const placeholders = ["E.g. DY Jets NLO",
                            "E.g. Graviton ggF madgraph",
                            "E.g. Higgs to Tau",
                            "E.g. QCD PSWeights",];
      const randomNumber = Math.floor(Math.random() * placeholders.length);
      return placeholders[randomNumber];
    },
  },
};
</script>

<style scoped>
.suggestion-list-wrapper {
  position: relative;
  z-index: 100;
}
.suggestion-list {
  margin: 2px;
  width: calc(100% - 4px);
  background: #fff;
  position: absolute;
  cursor: pointer;
}
.suggestion-item {
  padding: 4px;
  margin-top: 2px;
  margin-bottom: 2px;
  display: flex;
  letter-spacing: -0.2px;
  justify-content: space-between;
  font-size: 0.9em;
}
.suggestion-item-hover {
  background: #eeeeee;
}
</style>