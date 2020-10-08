<template>
  <div>
    <span style="vertical-align: middle;" class="mr-1"><slot></slot></span>
    <div class="button-group">
      <button v-for="pair in options"
              :key="pair[0]"
              class="button-group-button"
              v-bind:class="[selectedValue === pair[0] ? 'clicked' : '']"
              v-on:click="selectedValue = pair[0];">
        {{pair[1]}}
      </button>
    </div>
  </div>
</template>

<script>
  export default {
    props:{
      options: {
        type: Array,
        value: []
      },
    },
    data () {
      return {
        selectedValue: undefined,
      }
    },
    created () {
      if (this.options.length) {
        this.selectedValue = this.options[0][0];
      }
    },
    watch:{
      selectedValue: function (newValue, oldValue) {
        this.$emit('changed', this.selectedValue);
      },
      options: function(newValue, oldValue) {
        this.selectedValue = newValue[0][0];
      }
    }
  }
</script>

<style scoped>


.button-group {
  border-radius: 6px;
  border: solid 1px #aaa;
  color: var(--v-anchor-base);
  display: inline-block;
  font-size: 0.9em;
  background: white;
  overflow: hidden;
  vertical-align: middle;
}

.button-group-button {
  display: inline-block;
  padding: calc((28px - 0.9em) / 2) 8px;
  line-height: 0.9em;
  height: 28px;
}

.button-group-button:not(:first-child) {
  border-left: solid 1px #aaa;
}

.clicked {
  background-color: var(--v-anchor-base);
  color: white;
  font-weight: 500;
}

</style>