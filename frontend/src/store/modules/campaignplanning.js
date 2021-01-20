const state = {
    action: [],
    entry: [],
    entriesCopy: [],
    redoEntries: null,
    undoEntries: null
};

const getters = {
    getUndoEntry: state => {
        return state.entry;
    },
    getUndoAction: state => {
        return state.action;
    },
    popUndo: state => {
        state.action.pop();
        state.entry.pop();
    }
};

const actions = {};

const mutations = {
    commitEntries(state, payload) {
        state.action.push(payload.action);
        state.entry.push(payload.entry);

    },
    commitEntriesRedo(state, action, payload){
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