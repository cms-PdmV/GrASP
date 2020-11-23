import axios from 'axios';

const state = {
    entries: [] 
};

const getters = {};

const actions = {};

const mutations = {
    updateEntries(stat, payload) {
        state.entries.push(payload);
    },

    // empty state needed for the undo redo feature
    emptyState() {
        this.replaceState({ entries: [] });
    }
};

export default {
    state,
    getters,
    actions,
    mutations
}