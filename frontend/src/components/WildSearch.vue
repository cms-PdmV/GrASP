<template>
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
          @click="select(value)"
          @mouseover="mouseEnteredItem(index)"
          v-bind:class="{ 'suggestion-item-hover': index == selectedIndex }"
        >
          <div style="line-break: anywhere" v-html="highlight(value)"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from "axios";
/* component needs to do to be compatible with v-model
   is accept a :value property and emit an @input event
   when the user changes the value.
*/
export default {
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
    };
  },
  created() {},
  watch: {
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
      newValue = newValue.trim();
      if (newValue in this.cache) {
        this.items = this.cache[newValue];
        this.suggestionsTimer = undefined;
      } else {
        this.suggestionsTimer = setTimeout(() => {
          const component = this;
          component.suggestionsTimer = undefined;
          component.loading = true;
          axios.get("api/search?q=" + newValue).then((response) => {
            component.items = response.data.response;
            component.cache[newValue] = component.items;
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
      let url = window.location.origin + "/grasp/samples?dataset=" + value;
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
      const splitValues = this.value.toLowerCase().replace(/\*/g, " ").split(" ").filter(Boolean);
      let highlighted = "";
      let lastIndex = 0;
      const lowerCaseItem = item.toLowerCase();
      for (let split of splitValues) {
        let foundIndex = lowerCaseItem.indexOf(split, lastIndex);
        if (foundIndex < 0) {
          continue;
        }
        highlighted += item.slice(lastIndex, foundIndex);
        lastIndex += foundIndex - lastIndex;
        let highlightedPiece = item.slice(foundIndex, foundIndex + split.length);
        highlighted += '<b style="background: #dadada">' + highlightedPiece + '</b>';
        lastIndex += split.length;
      }
      highlighted += item.slice(lastIndex);
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