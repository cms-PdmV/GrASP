const state = {
    entriesCopy: [],
    redoEntries: null,
    undoEntries: null
};

const getters = {
    getUndoEntry () {
        return state.undoEntries;
    },
    getRedoEntry () {
        return state.redoEntries;
    }
};

const actions = {};

const mutations = {
    commitEntries(state, payload) {
        state.entriesCopy.push(payload);
    },
    commitEntriesRedo(state, payload){
        state.redoEntries = payload;
    },
    commitEntriesUndo(state, payload){
        state.undoEntries = payload;
    },

    // empty state needed for the undo redo feature
    emptyState() {
        this.replaceState({ entriesCopy : [] });
    }
};

export default {
    state,
    getters,
    actions,
    mutations
}