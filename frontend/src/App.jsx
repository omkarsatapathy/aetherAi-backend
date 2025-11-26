import { useEffect } from 'react';
import useStore from './store/useStore';
import SetupWizard from './components/setup/SetupWizard';
import ChatContainer from './components/chat/ChatContainer';
import { checkHealth, getModelProviders, getResponseStyles } from './services/api';

function App() {
  const { isSetupDone, setOnline, setError, theme, setTheme } = useStore();

  useEffect(() => {
    // Initialize theme
    document.documentElement.setAttribute('data-theme', theme);

    // Check server health
    const healthCheck = async () => {
      try {
        await checkHealth();
        setOnline(true);
      } catch (error) {
        console.error('Health check failed:', error);
        setOnline(false);
        setError('Unable to connect to server');
      }
    };

    healthCheck();

    // Load model providers and response styles
    const loadModels = async () => {
      try {
        const [providers, styles] = await Promise.all([
          getModelProviders(),
          getResponseStyles()
        ]);
        useStore.getState().setModelProviders(providers.providers || []);
        useStore.getState().setResponseStyles(styles.styles || []);

        // Set default model if not set
        if (providers.providers && providers.providers.length > 0) {
          const currentProvider = useStore.getState().modelProvider;
          if (!currentProvider) {
            useStore.getState().setModelProvider(providers.providers[0].id);
          }
        }
      } catch (error) {
        console.error('Failed to load models:', error);
      }
    };

    loadModels();

    // Network status listeners
    const handleOnline = () => {
      setOnline(true);
      healthCheck();
    };
    const handleOffline = () => setOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <div className="app">
      {!isSetupDone ? <SetupWizard /> : <ChatContainer />}
    </div>
  );
}

export default App;
