import { create } from 'zustand';
import { persist } from 'zustand/middleware';

const useStore = create(
  persist(
    (set, get) => ({
      // ============= Setup State =============
      isSetupDone: false,
      setSetupDone: (value) => set({ isSetupDone: value }),

      // ============= Theme State =============
      theme: 'light',
      toggleTheme: () => set((state) => {
        const newTheme = state.theme === 'light' ? 'dark' : 'light';
        document.documentElement.setAttribute('data-theme', newTheme);
        return { theme: newTheme };
      }),
      setTheme: (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        set({ theme });
      },

      // ============= Session State =============
      currentSessionId: null,
      sessions: [],
      setCurrentSessionId: (sessionId) => set({ currentSessionId: sessionId }),
      setSessions: (sessions) => set({ sessions }),
      addSession: (session) => set((state) => ({
        sessions: [session, ...state.sessions]
      })),
      removeSession: (sessionId) => set((state) => ({
        sessions: state.sessions.filter(s => s.session_id !== sessionId),
        currentSessionId: state.currentSessionId === sessionId ? null : state.currentSessionId
      })),

      // ============= Messages State =============
      messages: [],
      setMessages: (messages) => set({ messages }),
      addMessage: (message) => set((state) => ({
        messages: [...state.messages, message]
      })),
      updateLastMessage: (content) => set((state) => {
        const messages = [...state.messages];
        if (messages.length > 0) {
          messages[messages.length - 1] = {
            ...messages[messages.length - 1],
            content
          };
        }
        return { messages };
      }),
      clearMessages: () => set({ messages: [] }),

      // ============= Model & Response Style State =============
      modelProvider: '',
      responseStyle: 'Normal',
      modelProviders: [],
      responseStyles: [],
      setModelProvider: (provider) => set({ modelProvider: provider }),
      setResponseStyle: (style) => set({ responseStyle: style }),
      setModelProviders: (providers) => set({ modelProviders: providers }),
      setResponseStyles: (styles) => set({ responseStyles: styles }),

      // ============= Documents State =============
      documents: [],
      setDocuments: (documents) => set({ documents }),
      addDocument: (document) => set((state) => ({
        documents: [...state.documents, document]
      })),
      removeDocument: (documentId) => set((state) => ({
        documents: state.documents.filter(d => d.id !== documentId)
      })),

      // ============= Image State =============
      currentImage: null,
      setCurrentImage: (image) => set({ currentImage: image }),
      clearCurrentImage: () => set({ currentImage: null }),

      // ============= UI State =============
      isOnline: true,
      isSidebarOpen: false,
      isLoading: false,
      error: null,
      setOnline: (value) => set({ isOnline: value }),
      toggleSidebar: () => set((state) => ({ isSidebarOpen: !state.isSidebarOpen })),
      setSidebarOpen: (value) => set({ isSidebarOpen: value }),
      setLoading: (value) => set({ isLoading: value }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),

      // ============= Web Search State =============
      webSearchEnabled: false,
      toggleWebSearch: () => set((state) => ({ webSearchEnabled: !state.webSearchEnabled })),
      setWebSearchEnabled: (value) => set({ webSearchEnabled: value }),

      // ============= Setup Wizard State =============
      setupPage: 1,
      apiKeys: {
        openai: '',
        gemini: ''
      },
      setSetupPage: (page) => set({ setupPage: page }),
      setApiKey: (provider, key) => set((state) => ({
        apiKeys: {
          ...state.apiKeys,
          [provider]: key
        }
      })),
    }),
    {
      name: 'chatbot-storage',
      partialize: (state) => ({
        isSetupDone: state.isSetupDone,
        theme: state.theme,
        currentSessionId: state.currentSessionId,
        modelProvider: state.modelProvider,
        responseStyle: state.responseStyle,
      }),
    }
  )
);

export default useStore;
