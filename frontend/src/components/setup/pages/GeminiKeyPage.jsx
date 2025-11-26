import { useState } from 'react';

function GeminiKeyPage({ apiKey, onApiKeyChange, onNext, onPrev, onSkip }) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="setup-page active" data-page="4">
      <div className="setup-api-icon gemini">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z" fill="url(#gemini-gradient)"/>
          <defs>
            <linearGradient id="gemini-gradient" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" style={{stopColor:'#4285F4'}}/>
              <stop offset="25%" style={{stopColor:'#9B72CB'}}/>
              <stop offset="50%" style={{stopColor:'#D96570'}}/>
              <stop offset="100%" style={{stopColor:'#F9AB00'}}/>
            </linearGradient>
          </defs>
        </svg>
      </div>
      <h2 className="setup-title">Google Gemini API Key</h2>
      <p className="setup-description">
        Enter your Google Gemini API key. Get one from{' '}
        <a href="https://makersuite.google.com/app/apikey" target="_blank" rel="noopener">
          Google AI Studio
        </a>
      </p>
      <div className="setup-input-group">
        <div className="api-input-wrapper">
          <input
            type={showPassword ? 'text' : 'password'}
            className="api-input"
            placeholder="AIzaxxxxxxxxxxxxxxxxxxxxxxxx"
            value={apiKey}
            onChange={(e) => onApiKeyChange(e.target.value)}
            autoComplete="off"
          />
          <button
            className="toggle-visibility"
            type="button"
            title="Show/Hide"
            onClick={() => setShowPassword(!showPassword)}
          >
            {showPassword ? (
              <svg className="eye-off-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path>
                <line x1="1" y1="1" x2="23" y2="23"></line>
              </svg>
            ) : (
              <svg className="eye-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path>
                <circle cx="12" cy="12" r="3"></circle>
              </svg>
            )}
          </button>
        </div>
      </div>
      <div className="setup-actions">
        <button className="setup-btn secondary" onClick={onPrev}>
          Back
        </button>
        <button className="setup-btn tertiary" onClick={onSkip}>
          Skip
        </button>
        <button className="setup-btn primary" onClick={onNext}>
          Continue
        </button>
      </div>
    </div>
  );
}

export default GeminiKeyPage;
