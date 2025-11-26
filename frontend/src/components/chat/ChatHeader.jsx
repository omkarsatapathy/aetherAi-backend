import { useState } from 'react';
import useStore from '../../store/useStore';
import DeleteConfirmDialog from '../common/DeleteConfirmDialog';

function ChatHeader() {
  const [clearConfirmOpen, setClearConfirmOpen] = useState(false);

  const {
    modelProvider,
    setModelProvider,
    modelProviders,
    theme,
    toggleTheme,
    isOnline
  } = useStore();

  const handleClearClick = () => {
    setClearConfirmOpen(true);
  };

  const handleClearConfirm = async () => {
    useStore.getState().clearMessages();
    const { createSession } = await import('../../services/api');
    const newSession = await createSession();
    useStore.getState().setCurrentSessionId(newSession.session_id);
    setClearConfirmOpen(false);
  };

  const handleClearCancel = () => {
    setClearConfirmOpen(false);
  };

  return (
    <div className="chat-header">
      <div className="header-content">
        <div className="header-left">
          <div className="model-selector-wrapper">
            <select
              id="modelProvider"
              className="model-provider-select"
              value={modelProvider}
              onChange={(e) => setModelProvider(e.target.value)}
              title="Select Model Provider"
            >
              {modelProviders.length === 0 ? (
                <option value="">Loading...</option>
              ) : (
                modelProviders.map((provider) => (
                  <option key={provider.id} value={provider.id}>
                    {provider.name}
                  </option>
                ))
              )}
            </select>
            <svg className="dropdown-icon" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6 9l6 6 6-6"></path>
            </svg>
          </div>
        </div>

        <div className="header-center">
          <img src="/src/assets/images/logo.png" alt="Logo" className="header-logo" />
        </div>

        <div className="header-right">
          <div className="status-indicator" id="status">
            <span className={`status-dot ${isOnline ? 'online' : 'offline'}`}></span>
            <span className="status-text">{isOnline ? 'Ready' : 'Offline'}</span>
          </div>

          <button
            id="themeToggle"
            className="theme-toggle icon-button"
            title="Toggle theme (Dark/Light Mode)"
            onClick={toggleTheme}
            style={{ display: 'flex' }}
          >
            {theme === 'light' ? (
              <svg className="moon-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path>
              </svg>
            ) : (
              <svg className="sun-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="12" cy="12" r="5"></circle>
                <line x1="12" y1="1" x2="12" y2="3"></line>
                <line x1="12" y1="21" x2="12" y2="23"></line>
                <line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line>
                <line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line>
                <line x1="1" y1="12" x2="3" y2="12"></line>
                <line x1="21" y1="12" x2="23" y2="12"></line>
                <line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line>
                <line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line>
              </svg>
            )}
          </button>

          <button
            id="clearButton"
            className="icon-button"
            title="Clear current chat"
            onClick={handleClearClick}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"></path>
            </svg>
          </button>
        </div>
      </div>

      <DeleteConfirmDialog
        isOpen={clearConfirmOpen}
        onConfirm={handleClearConfirm}
        onCancel={handleClearCancel}
        title="Clear this chat?"
      />
    </div>
  );
}

export default ChatHeader;
