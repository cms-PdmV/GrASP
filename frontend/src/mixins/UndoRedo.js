const EMPTY_STATE = 'emptyState';

export const undoRedo = {
    data() {
        return {
          done: [],
          undone: []
        };
      },
      created() {
        if (this.$store) {
          this.$store.subscribe(mutation => {
            if (mutation.type !== EMPTY_STATE) {
              this.done.push(mutation);
            }
          });
        }
      },
      computed: {
        canRedo() {
          return this.undone.length;
        },
        canUndo() {
          return this.done.length;
        }
      },
      methods: {
        redo() {
            let commit = this.undone.pop();
            this.$store.commit('commitEntriesRedo', commit.payload);
        },
        undo() {
            let mutation = this.done.pop();
            this.$store.commit('commitEntriesUndo', mutation.payload);
            this.undone.push(mutation); 
            this.done.pop();      
        }
      }
}
