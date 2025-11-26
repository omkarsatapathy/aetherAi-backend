import { useState } from 'react';
import { downloadModel } from '../../../services/api';

function ModelDownloadPage({ onFinish, onPrev, onSkip }) {
  const [modelStatus, setModelStatus] = useState({
    'gpt-oss': 'ready', // ready, downloading, downloaded, error
    'qwen3': 'ready'
  });
  const [progress, setProgress] = useState({
    'gpt-oss': 0,
    'qwen3': 0
  });
  const [terminalOutput, setTerminalOutput] = useState('');
  const [showTerminal, setShowTerminal] = useState(false);
  const [currentDownload, setCurrentDownload] = useState(null);

  const handleDownload = (modelType) => {
    setCurrentDownload(modelType);
    setShowTerminal(true);
    setModelStatus(prev => ({ ...prev, [modelType]: 'downloading' }));
    setTerminalOutput('');

    downloadModel(
      modelType,
      (data) => {
        // On progress
        if (data.output) {
          setTerminalOutput(prev => prev + data.output + '\n');
        }
        if (data.progress !== undefined) {
          setProgress(prev => ({ ...prev, [modelType]: data.progress }));
        }
      },
      (error) => {
        // On error
        setModelStatus(prev => ({ ...prev, [modelType]: 'error' }));
        setTerminalOutput(prev => prev + '\nError: Download failed\n');
      },
      (data) => {
        // On complete
        setModelStatus(prev => ({ ...prev, [modelType]: 'downloaded' }));
        setTerminalOutput(prev => prev + '\n✓ Download completed successfully!\n');
        setCurrentDownload(null);
      }
    );
  };

  const models = [
    {
      id: 'gpt-oss',
      name: 'GPT-OSS-20B',
      description: 'General purpose, high quality responses',
      size: '~13.8 GB'
    },
    {
      id: 'qwen3',
      name: 'Qwen3-8B',
      description: 'Fast, efficient multilingual model',
      size: '~5.2 GB'
    }
  ];

  return (
    <div className="setup-page active" data-page="6">
      <div className="setup-api-icon">
        <svg width="80" height="80" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
          <polyline points="7 10 12 15 17 10"></polyline>
          <line x1="12" y1="15" x2="12" y2="3"></line>
        </svg>
      </div>
      <h2 className="setup-title">Select AI Model</h2>
      <p className="setup-description">
        Choose a model for local AI inference. Download it first, then it will be used to start the local server.
      </p>

      <p className="setup-note">
        <strong>Note:</strong> Models are large files and may take several minutes to download depending on your internet speed.
      </p>

      {models.map((model) => (
        <div key={model.id} className="model-card" data-model={model.id}>
          <div className="model-card-header">
            <div className="model-card-info">
              <div className="model-name">{model.name}</div>
              <div className="model-desc">{model.description}</div>
            </div>
            <div className="model-card-meta">
              <div className="model-size">{model.size}</div>
              <button
                className="model-download-btn"
                onClick={() => handleDownload(model.id)}
                disabled={modelStatus[model.id] === 'downloading' || modelStatus[model.id] === 'downloaded'}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>
                  <polyline points="7 10 12 15 17 10"></polyline>
                  <line x1="12" y1="15" x2="12" y2="3"></line>
                </svg>
                {modelStatus[model.id] === 'downloaded' ? 'Downloaded' :
                 modelStatus[model.id] === 'downloading' ? 'Downloading...' : 'Download'}
              </button>
            </div>
          </div>

          {modelStatus[model.id] === 'downloading' && (
            <div className="model-progress-container">
              <div className="model-progress-bar">
                <div className="model-progress-fill" style={{ width: `${progress[model.id]}%` }}></div>
              </div>
              <div className="model-progress-text">
                <span className="model-progress-percent">{progress[model.id]}%</span>
              </div>
            </div>
          )}

          <div className="model-status">
            <span className="status-text">
              {modelStatus[model.id] === 'ready' && 'Ready to download'}
              {modelStatus[model.id] === 'downloading' && 'Downloading...'}
              {modelStatus[model.id] === 'downloaded' && '✓ Downloaded'}
              {modelStatus[model.id] === 'error' && 'Download failed'}
            </span>
          </div>
        </div>
      ))}

      {showTerminal && (
        <div className="terminal-container">
          <div className="terminal-header">
            <span className="terminal-title">Download Output</span>
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
        <button className="setup-btn primary" onClick={onFinish}>
          Finish Setup
        </button>
      </div>
    </div>
  );
}

export default ModelDownloadPage;
