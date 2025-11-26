import { useState, useRef, useEffect } from 'react';
import useStore from '../../store/useStore';
import { sendChatMessage, saveMessage, uploadDocument } from '../../services/api';
import InputActions from './InputActions';
import CameraModal from './CameraModal';

function ChatInput() {
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [isCameraOpen, setIsCameraOpen] = useState(false);
  const textareaRef = useRef(null);
  const eventSourceRef = useRef(null);

  const {
    currentSessionId,
    modelProvider,
    responseStyle,
    webSearchEnabled,
    documents,
    currentImage,
    addMessage,
    updateLastMessage,
    addDocument,
    setCurrentImage,
    clearCurrentImage,
  } = useStore();

  useEffect(() => {
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  }, [input]);

  const handleSend = async () => {
    if (!input.trim() || !currentSessionId || isStreaming) return;

    const userMessage = input.trim();
    setInput('');
    setIsStreaming(true);

    // Add user message
    addMessage({ role: 'user', content: userMessage });

    // Save user message
    await saveMessage(currentSessionId, 'user', userMessage);

    // Add empty assistant message that will be streamed
    addMessage({ role: 'assistant', content: '' });

    let fullResponse = '';

    // Start streaming
    eventSourceRef.current = sendChatMessage(
      userMessage,
      currentSessionId,
      modelProvider,
      responseStyle,
      webSearchEnabled,
      documents.map(d => d.id),
      currentImage,
      (data) => {
        // On message chunk
        if (data.content) {
          fullResponse += data.content;
          updateLastMessage(fullResponse);
        }
      },
      (error) => {
        // On error
        console.error('Chat error:', error);
        updateLastMessage(fullResponse + '\n\n[Error: Failed to get response]');
        setIsStreaming(false);
      },
      async (data) => {
        // On complete
        setIsStreaming(false);
        // Save assistant message
        await saveMessage(currentSessionId, 'assistant', fullResponse);
      }
    );
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleStop = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      setIsStreaming(false);
    }
  };

  const handleDocumentUpload = async (file) => {
    if (!currentSessionId) {
      alert('Please start a chat session first');
      return;
    }

    try {
      const response = await uploadDocument(currentSessionId, file);
      addDocument({
        id: response.document_id,
        name: file.name,
        size: file.size
      });
    } catch (error) {
      console.error('Document upload failed:', error);
      alert('Failed to upload document. Please try again.');
    }
  };

  const handleImageUpload = (file) => {
    const reader = new FileReader();
    reader.onload = (e) => {
      setCurrentImage(e.target.result);
    };
    reader.readAsDataURL(file);
  };

  const handleCameraClick = () => {
    setIsCameraOpen(true);
  };

  const handleCameraClose = () => {
    setIsCameraOpen(false);
  };

  return (
    <>
      <div className="chat-input-container">
        {/* Image preview */}
        {currentImage && (
          <div className="image-preview-area">
            <div className="image-preview-container">
              <img src={currentImage} alt="Preview" />
              <button
                className="remove-image-btn"
                onClick={clearCurrentImage}
                title="Remove image"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
        )}

        <div className="input-wrapper">
          <InputActions
            onDocumentUpload={handleDocumentUpload}
            onImageUpload={handleImageUpload}
            onCameraClick={handleCameraClick}
          />
          <textarea
            ref={textareaRef}
            id="messageInput"
            placeholder="Message AI Chatbot"
            rows="1"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={isStreaming}
          />
          {isStreaming ? (
            <button
              className="send-button stop"
              title="Stop generating"
              onClick={handleStop}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                <rect x="6" y="6" width="12" height="12" />
              </svg>
            </button>
          ) : (
            <button
              id="sendButton"
              className="send-button"
              title="Send message"
              onClick={handleSend}
              disabled={!input.trim()}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <line x1="22" y1="2" x2="11" y2="13"></line>
                <polygon points="22 2 15 22 11 13 2 9 22 2"></polygon>
              </svg>
            </button>
          )}
        </div>
      </div>

      <CameraModal isOpen={isCameraOpen} onClose={handleCameraClose} />
    </>
  );
}

export default ChatInput;
