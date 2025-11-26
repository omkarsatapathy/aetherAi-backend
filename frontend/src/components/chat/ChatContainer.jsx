import { useEffect, useState } from 'react';
import useStore from '../../store/useStore';
import ChatHeader from './ChatHeader';
import ChatMessages from './ChatMessages';
import ChatInput from './ChatInput';
import Sidebar from '../session/Sidebar';
import { listSessions, createSession, getMessages, getModelProviders, getResponseStyles } from '../../services/api';

function ChatContainer() {
  const {
    currentSessionId,
    setCurrentSessionId,
    setSessions,
    messages,
    setMessages,
    isSidebarOpen,
    setModelProviders,
    setResponseStyles,
    setModelProvider,
    modelProvider,
  } = useStore();

  useEffect(() => {
    // Load initial data on mount
    const loadInitialData = async () => {
      try {
        // Load model providers
        const providersData = await getModelProviders();
        if (providersData.providers && providersData.providers.length > 0) {
          setModelProviders(providersData.providers);
          // Set first provider as default if none selected
          if (!modelProvider) {
            setModelProvider(providersData.providers[0].id);
          }
        }

        // Load response styles
        const stylesData = await getResponseStyles();
        if (stylesData.styles && stylesData.styles.length > 0) {
          setResponseStyles(stylesData.styles);
        }

        // Load sessions
        const data = await listSessions();
        setSessions(data.sessions || []);

        // Create new session if none exists
        if (!currentSessionId && (!data.sessions || data.sessions.length === 0)) {
          const newSession = await createSession();
          setCurrentSessionId(newSession.session_id);
        } else if (!currentSessionId && data.sessions && data.sessions.length > 0) {
          setCurrentSessionId(data.sessions[0].session_id);
        }
      } catch (error) {
        console.error('Failed to load initial data:', error);
      }
    };

    loadInitialData();
  }, []);

  useEffect(() => {
    // Load messages when session changes
    const loadSessionMessages = async () => {
      if (currentSessionId) {
        try {
          const data = await getMessages(currentSessionId);
          setMessages(data.messages || []);
        } catch (error) {
          console.error('Failed to load messages:', error);
        }
      }
    };

    loadSessionMessages();
  }, [currentSessionId]);

  return (
    <div className="container">
      {/* Sidebar overlay for mobile */}
      <div
        className="sidebar-overlay"
        style={{ display: isSidebarOpen ? 'block' : 'none' }}
        onClick={() => useStore.getState().setSidebarOpen(false)}
      ></div>

      <Sidebar />

      {/* Toggle button for mobile */}
      <button
        className="sidebar-toggle"
        onClick={() => useStore.getState().toggleSidebar()}
      >
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <line x1="3" y1="12" x2="21" y2="12"></line>
          <line x1="3" y1="6" x2="21" y2="6"></line>
          <line x1="3" y1="18" x2="21" y2="18"></line>
        </svg>
      </button>

      <div className="chat-container">
        <ChatHeader />
        <ChatMessages />
        <ChatInput />
      </div>
    </div>
  );
}

export default ChatContainer;
