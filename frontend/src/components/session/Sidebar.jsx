import { useState } from 'react';
import useStore from '../../store/useStore';
import { createSession, deleteSession, getMessages } from '../../services/api';
import DeleteConfirmDialog from '../common/DeleteConfirmDialog';

function Sidebar() {
  const [deleteConfirmOpen, setDeleteConfirmOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState(null);

  const {
    sessions,
    currentSessionId,
    setCurrentSessionId,
    setSessions,
    setMessages,
    isSidebarOpen,
    setSidebarOpen,
  } = useStore();

  const handleNewChat = async () => {
    try {
      const newSession = await createSession();
      setCurrentSessionId(newSession.session_id);
      setMessages([]);
      setSessions([newSession, ...sessions]);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleLoadSession = async (sessionId) => {
    try {
      setCurrentSessionId(sessionId);
      const data = await getMessages(sessionId);
      setMessages(data.messages || []);
      setSidebarOpen(false);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const handleDeleteClick = (e, sessionId) => {
    e.stopPropagation();
    setSessionToDelete(sessionId);
    setDeleteConfirmOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (!sessionToDelete) return;

    try {
      await deleteSession(sessionToDelete);
      setSessions(sessions.filter(s => s.session_id !== sessionToDelete));

      if (currentSessionId === sessionToDelete) {
        // Create new session if deleted current
        await handleNewChat();
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    } finally {
      setDeleteConfirmOpen(false);
      setSessionToDelete(null);
    }
  };

  const handleDeleteCancel = () => {
    setDeleteConfirmOpen(false);
    setSessionToDelete(null);
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  return (
    <div className={`sidebar ${isSidebarOpen ? 'open' : ''}`} id="sidebar">
      <div className="sidebar-header">
        <button
          id="newChatButton"
          className="new-chat-button"
          title="New Chat"
          onClick={handleNewChat}
        >
          <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 5v14M5 12h14"></path>
          </svg>
          <span>New chat</span>
        </button>
      </div>

      <div className="session-list" id="sessionList">
        {sessions.length === 0 ? (
          <div style={{ padding: '20px', textAlign: 'center', color: '#8696a0', fontSize: '14px' }}>
            No chat history yet
          </div>
        ) : (
          sessions.map((session) => (
            <div
              key={session.session_id}
              className={`session-item ${session.session_id === currentSessionId ? 'active' : ''}`}
              onClick={() => handleLoadSession(session.session_id)}
            >
              <div style={{ flex: 1, minWidth: 0 }}>
                <div className="session-title">{session.title}</div>
                <div className="session-date">{formatDate(session.updated_at)}</div>
              </div>
              <button
                className="session-delete"
                title="Delete chat"
                onClick={(e) => handleDeleteClick(e, session.session_id)}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2"></path>
                </svg>
              </button>
            </div>
          ))
        )}
      </div>

      <DeleteConfirmDialog
        isOpen={deleteConfirmOpen}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        title="Delete this chat?"
      />
    </div>
  );
}

export default Sidebar;
