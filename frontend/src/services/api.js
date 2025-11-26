import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || window.location.origin;

// Create axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error);
    return Promise.reject(error);
  }
);

// ============= Health Check =============
export const checkHealth = async () => {
  const response = await apiClient.get('/api/health');
  return response.data;
};

// ============= Sessions =============
export const createSession = async (title = 'New Chat') => {
  const response = await apiClient.post('/api/sessions', { title });
  return response.data;
};

export const listSessions = async (limit = 50) => {
  const response = await apiClient.get(`/api/sessions?limit=${limit}`);
  return response.data;
};

export const getSession = async (sessionId, includeMessages = true) => {
  const response = await apiClient.get(
    `/api/sessions/${sessionId}?include_messages=${includeMessages}`
  );
  return response.data;
};

export const deleteSession = async (sessionId) => {
  const response = await apiClient.delete(`/api/sessions/${sessionId}`);
  return response.data;
};

// ============= Messages =============
export const saveMessage = async (sessionId, role, content) => {
  const response = await apiClient.post('/api/messages', {
    session_id: sessionId,
    role,
    content,
  });
  return response.data;
};

export const getMessages = async (sessionId) => {
  const response = await apiClient.get(`/api/messages/${sessionId}`);
  return response.data;
};

export const deleteMessage = async (sessionId, messageId) => {
  const response = await apiClient.delete(`/api/messages/${sessionId}/${messageId}`);
  return response.data;
};

// ============= Chat (SSE Streaming) =============
export const sendChatMessage = (
  message,
  sessionId,
  modelProvider,
  responseStyle,
  webSearch,
  documents,
  image,
  onMessage,
  onError,
  onComplete
) => {
  const url = new URL(`${API_BASE_URL}/api/chat/stream`);
  const params = {
    session_id: sessionId,
    message,
    model_provider: modelProvider,
    response_style: responseStyle,
    web_search: webSearch,
  };

  // Add documents if provided
  if (documents && documents.length > 0) {
    params.documents = JSON.stringify(documents);
  }

  // Add image if provided
  if (image) {
    params.image = image;
  }

  Object.keys(params).forEach(key => url.searchParams.append(key, params[key]));

  const eventSource = new EventSource(url.toString());

  // Listen for 'connected' event
  eventSource.addEventListener('connected', (event) => {
    console.log('Connected to chat stream');
  });

  // Listen for 'thinking' event
  eventSource.addEventListener('thinking', (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('Thinking:', data.status);
    } catch (error) {
      console.error('Error parsing thinking event:', error);
    }
  });

  // Listen for 'message' event (actual content chunks)
  eventSource.addEventListener('message', (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.chunk) {
        // Convert chunk to content for ChatInput compatibility
        onMessage && onMessage({ content: data.chunk });
      }
    } catch (error) {
      console.error('Error parsing message event:', error);
      onError && onError(error);
    }
  });

  // Listen for 'done' event (completion)
  eventSource.addEventListener('done', (event) => {
    try {
      const data = JSON.parse(event.data);
      eventSource.close();
      onComplete && onComplete(data);
    } catch (error) {
      console.error('Error parsing done event:', error);
      eventSource.close();
      onError && onError(error);
    }
  });

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
    onError && onError(error);
  };

  return eventSource;
};

// ============= Documents =============
export const uploadDocument = async (sessionId, file) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('session_id', sessionId);

  const response = await apiClient.post('/api/documents/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getSessionDocuments = async (sessionId) => {
  const response = await apiClient.get(`/api/documents/${sessionId}`);
  return response.data;
};

export const deleteDocument = async (documentId) => {
  const response = await apiClient.delete(`/api/documents/${documentId}`);
  return response.data;
};

// ============= Models =============
export const getModelProviders = async () => {
  const response = await apiClient.get('/api/models/providers');
  return response.data;
};

export const getResponseStyles = async () => {
  const response = await apiClient.get('/api/models/styles');
  return response.data;
};

// ============= Setup =============
export const checkSetupStatus = async () => {
  const response = await apiClient.get('/api/setup/status');
  return response.data;
};

export const saveApiKeys = async (openaiKey, geminiKey) => {
  const response = await apiClient.post('/api/setup/keys', {
    openai_key: openaiKey,
    gemini_key: geminiKey,
  });
  return response.data;
};

export const installLlamaCpp = (onProgress, onError, onComplete) => {
  const url = `${API_BASE_URL}/api/setup/llama/install`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.done) {
        eventSource.close();
        onComplete && onComplete(data);
      } else {
        onProgress && onProgress(data);
      }
    } catch (error) {
      console.error('Error parsing SSE message:', error);
      onError && onError(error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
    onError && onError(error);
  };

  return eventSource;
};

export const downloadModel = (modelType, onProgress, onError, onComplete) => {
  const url = `${API_BASE_URL}/api/setup/models/download?model=${modelType}`;
  const eventSource = new EventSource(url);

  eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.done) {
        eventSource.close();
        onComplete && onComplete(data);
      } else {
        onProgress && onProgress(data);
      }
    } catch (error) {
      console.error('Error parsing SSE message:', error);
      onError && onError(error);
    }
  };

  eventSource.onerror = (error) => {
    console.error('SSE Error:', error);
    eventSource.close();
    onError && onError(error);
  };

  return eventSource;
};

export const checkModelStatus = async (modelType) => {
  const response = await apiClient.get(`/api/setup/models/status?model=${modelType}`);
  return response.data;
};

// ============= Images =============
export const uploadImage = async (file) => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await apiClient.post('/api/image/upload', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const analyzeImage = async (imageUrl, prompt) => {
  const response = await apiClient.post('/api/image/analyze', {
    image_url: imageUrl,
    prompt,
  });
  return response.data;
};

// ============= Voice =============
export const textToSpeech = async (text) => {
  const response = await apiClient.post('/api/voice/tts', { text }, {
    responseType: 'blob',
  });
  return response.data;
};

// ============= Config =============
export const getConfig = async () => {
  const response = await apiClient.get('/api/config');
  return response.data;
};

export const updateConfig = async (config) => {
  const response = await apiClient.put('/api/config', config);
  return response.data;
};

export default apiClient;
