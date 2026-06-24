import { create } from 'zustand';

/**
 * Global application state extracted from App.jsx to reduce render thrashing.
 * Primarily handles high-frequency mutation states (e.g., drag and drop coordinates,
 * graph layouts, and global student/session tracking).
 */
const useAppStore = create((set) => ({
  // Core Session State
  selectedStudent: null,
  setSelectedStudent: (student) => set({ selectedStudent: student }),

  // High-frequency layout states (e.g. for ReactFlow / DnD)
  graphNodes: [],
  setGraphNodes: (nodes) => set({ graphNodes: nodes }),
  
  graphEdges: [],
  setGraphEdges: (edges) => set({ graphEdges: edges }),

  // Theme / Experience states
  globalTheme: 'space',
  setGlobalTheme: (theme) => set({ globalTheme: theme }),
  
  // Modals & UI Toggles
  isMapModalOpen: false,
  setMapModalOpen: (isOpen) => set({ isMapModalOpen: isOpen }),

  // Reset function to clear session
  resetSession: () => set({ 
    selectedStudent: null, 
    graphNodes: [], 
    graphEdges: [],
    isMapModalOpen: false 
  })
}));

export default useAppStore;
