import { useState } from 'react';
import useStore from '../../store/useStore';
import WelcomePage from './pages/WelcomePage';
import FeaturesPage from './pages/FeaturesPage';
import OpenAIKeyPage from './pages/OpenAIKeyPage';
import GeminiKeyPage from './pages/GeminiKeyPage';
import LlamaSetupPage from './pages/LlamaSetupPage';
import ModelDownloadPage from './pages/ModelDownloadPage';

function SetupWizard() {
  const { setSetupDone } = useStore();
  const [currentPage, setCurrentPage] = useState(1);
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    gemini: ''
  });
  const [showSkipWarning, setShowSkipWarning] = useState(false);
  const [pendingSkipType, setPendingSkipType] = useState(null);

  const totalPages = 6;

  const handleNext = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    } else {
      handleFinish();
    }
  };

  const handlePrev = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleSkip = (skipType) => {
    setPendingSkipType(skipType);
    setShowSkipWarning(true);
  };

  const confirmSkip = () => {
    setShowSkipWarning(false);
    setPendingSkipType(null);
    handleNext();
  };

  const cancelSkip = () => {
    setShowSkipWarning(false);
    setPendingSkipType(null);
  };

  const handleFinish = () => {
    // Save API keys if provided
    if (apiKeys.openai || apiKeys.gemini) {
      import('../../services/api').then(({ saveApiKeys }) => {
        saveApiKeys(apiKeys.openai, apiKeys.gemini).catch(console.error);
      });
    }

    setSetupDone(true);
  };

  const updateApiKey = (provider, value) => {
    setApiKeys(prev => ({
      ...prev,
      [provider]: value
    }));
  };

  const renderPage = () => {
    switch (currentPage) {
      case 1:
        return <WelcomePage onNext={handleNext} />;
      case 2:
        return <FeaturesPage onNext={handleNext} onPrev={handlePrev} />;
      case 3:
        return (
          <OpenAIKeyPage
            apiKey={apiKeys.openai}
            onApiKeyChange={(value) => updateApiKey('openai', value)}
            onNext={handleNext}
            onPrev={handlePrev}
            onSkip={() => handleSkip('openai')}
          />
        );
      case 4:
        return (
          <GeminiKeyPage
            apiKey={apiKeys.gemini}
            onApiKeyChange={(value) => updateApiKey('gemini', value)}
            onNext={handleNext}
            onPrev={handlePrev}
            onSkip={() => handleSkip('gemini')}
          />
        );
      case 5:
        return (
          <LlamaSetupPage
            onNext={handleNext}
            onPrev={handlePrev}
            onSkip={() => handleSkip('llama')}
          />
        );
      case 6:
        return (
          <ModelDownloadPage
            onFinish={handleFinish}
            onPrev={handlePrev}
            onSkip={() => handleSkip('model')}
          />
        );
      default:
        return <WelcomePage onNext={handleNext} />;
    }
  };

  return (
    <>
      <div className="setup-overlay" style={{ display: 'flex' }}>
        <div className="setup-backdrop"></div>
        <div className="setup-wizard">
          {renderPage()}

          {/* Page dots */}
          <div className="setup-dots">
            {[1, 2, 3, 4, 5, 6].map((page) => (
              <span
                key={page}
                className={`dot ${page === currentPage ? 'active' : ''}`}
              ></span>
            ))}
          </div>
        </div>
      </div>

      {/* Skip Warning Modal */}
      {showSkipWarning && (
        <div className="skip-warning-modal" style={{ display: 'flex' }}>
          <div className="skip-warning-backdrop" onClick={cancelSkip}></div>
          <div className="skip-warning-content">
            <div className="warning-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                <line x1="12" y1="9" x2="12" y2="13"></line>
                <line x1="12" y1="17" x2="12.01" y2="17"></line>
              </svg>
            </div>
            <h3>Skip Configuration?</h3>
            <p>
              {pendingSkipType === 'openai' && 'Without an OpenAI API key, OpenAI models will not be available.'}
              {pendingSkipType === 'gemini' && 'Without a Gemini API key, Google Gemini models will not be available.'}
              {pendingSkipType === 'llama' && 'Without llama.cpp, local AI models will not be available.'}
              {pendingSkipType === 'model' && 'Without downloading a model, you won\'t be able to use local AI inference.'}
            </p>
            <div className="warning-actions">
              <button className="setup-btn secondary" onClick={cancelSkip}>
                Go Back
              </button>
              <button className="setup-btn tertiary" onClick={confirmSkip}>
                Skip Anyway
              </button>
            </div>
          </div>
        </div>
      )}
    </>
  );
}

export default SetupWizard;
