function WelcomePage({ onNext }) {
  return (
    <div className="setup-page active" data-page="1">
      <div className="setup-logo">
        <div className="logo-icon">
          <img src="/src/assets/images/logo.png" alt="Logo" />
        </div>
      </div>
      <h1 className="setup-title">Welcome to AI Chatbot</h1>
      <p className="setup-description">
        Your intelligent assistant powered by multiple AI models. Let's get you set up in just a few steps.
      </p>
      <div className="setup-actions">
        <button className="setup-btn primary" onClick={onNext}>
          Get Started
        </button>
      </div>
    </div>
  );
}

export default WelcomePage;
