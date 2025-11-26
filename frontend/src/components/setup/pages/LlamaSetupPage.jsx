import { useState, useEffect } from 'react';
import { installLlamaCpp } from '../../../services/api';

function LlamaSetupPage({ onNext, onPrev, onSkip }) {
  const [status, setStatus] = useState('checking'); // checking, not_installed, installing, installed, error
  const [terminalOutput, setTerminalOutput] = useState('');
  const [showTerminal, setShowTerminal] = useState(false);

  useEffect(() => {
    // Check if llama.cpp is already installed
    // For now, assume not installed
    setStatus('not_installed');
  }, []);

  const handleInstall = () => {
    setStatus('installing');
    setShowTerminal(true);
    setTerminalOutput('Starting llama.cpp installation...\n');

    installLlamaCpp(
      (data) => {
        // On progress
        if (data.output) {
          setTerminalOutput(prev => prev + data.output + '\n');
        }
      },
      (error) => {
        // On error
        setStatus('error');
        setTerminalOutput(prev => prev + '\nError: Installation failed\n');
      },
      (data) => {
        // On complete
        setStatus('installed');
        setTerminalOutput(prev => prev + '\n✓ Installation completed successfully!\n');
      }
    );
  };

  return (
    <div className="setup-page active" data-page="5">
      <div className="setup-api-icon llama">
        <img src="/src/assets/images/llama.png" alt="llama.cpp" className="llama-logo" />
      </div>
      <h2 className="setup-title">Local LLM Setup</h2>
      <p className="setup-description">
        Set up llama.cpp to run AI models locally on your machine. This enables offline usage with no API costs.
      </p>

      <div className="llama-status">
        {status === 'checking' && <div className="status-checking">Checking installation status...</div>}
        {status === 'not_installed' && <div className="status-not-installed">llama.cpp is not installed</div>}
        {status === 'installing' && <div className="status-installing">Installing llama.cpp...</div>}
        {status === 'installed' && <div className="status-installed">✓ llama.cpp is installed</div>}
        {status === 'error' && <div className="status-error">Installation failed</div>}
      </div>

      {showTerminal && (
        <div className="terminal-container">
          <div className="terminal-header">
            <span className="terminal-title">Terminal Output</span>
          </div>
          <div className="terminal-output">
            <pre>{terminalOutput}</pre>
          </div>
        </div>
      )}

      <div className="setup-actions">
        <button className="setup-btn secondary" onClick={onPrev}>
          Back
        </button>
        <button className="setup-btn tertiary" onClick={onSkip}>
          Skip
        </button>
        {status === 'not_installed' && (
          <button className="setup-btn primary" onClick={handleInstall}>
            Install llama.cpp
          </button>
        )}
        {(status === 'installed' || status === 'error') && (
          <button className="setup-btn primary" onClick={onNext}>
            Continue
          </button>
        )}
        {status === 'installing' && (
          <button className="setup-btn primary" disabled>
            Installing...
          </button>
        )}
      </div>
    </div>
  );
}

export default LlamaSetupPage;
