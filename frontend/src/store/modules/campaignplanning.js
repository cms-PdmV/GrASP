const state = {
    entriesCopy: [] 
};

const getters = {
    eventEntries: (state) => state.entriesCopy
};

const actions = {};

const mutations = {
    commitEntries(state, payload) {
        state.entriesCopy.push(payload);
    }
};

export default {
    state,
    getters,
    actions,
    mutations
}