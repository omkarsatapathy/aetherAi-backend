function FeaturesPage({ onNext, onPrev }) {
  return (
    <div className="setup-page active" data-page="2">
      <div className="setup-features">
        <div className="feature-item">
          <div className="feature-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"></path>
            </svg>
          </div>
          <div className="feature-text">
            <h3>Multi-Model Chat</h3>
            <p>Chat with OpenAI GPT, Google Gemini, or local LLMs</p>
          </div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
              <polyline points="14 2 14 8 20 8"></polyline>
            </svg>
          </div>
          <div className="feature-text">
            <h3>Document Analysis</h3>
            <p>Upload PDFs, docs, and text files for AI-powered analysis</p>
          </div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <circle cx="12" cy="12" r="10"></circle>
              <line x1="2" y1="12" x2="22" y2="12"></line>
              <path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path>
            </svg>
          </div>
          <div className="feature-text">
            <h3>Web Search</h3>
            <p>Search the web and get AI-summarized results</p>
          </div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"></path>
              <path d="M19 10v2a7 7 0 0 1-14 0v-2"></path>
              <line x1="12" y1="19" x2="12" y2="23"></line>
              <line x1="8" y1="23" x2="16" y2="23"></line>
            </svg>
          </div>
          <div className="feature-text">
            <h3>Voice Support</h3>
            <p>Text-to-speech responses for a natural experience</p>
          </div>
        </div>
      </div>
      <div className="setup-actions">
        <button className="setup-btn secondary" onClick={onPrev}>
          Back
        </button>
        <button className="setup-btn primary" onClick={onNext}>
          Continue
        </button>
      </div>
    </div>
  );
}

export default FeaturesPage;
