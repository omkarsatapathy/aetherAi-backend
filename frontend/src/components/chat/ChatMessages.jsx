import { useEffect, useRef } from 'react';
import useStore from '../../store/useStore';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import MessageActions from './MessageActions';

function ChatMessages() {
  const { messages } = useStore();
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="chat-messages" id="chatMessages">
        <div className="chat-welcome" id="chatWelcome">
          <img src="/src/assets/images/logo.png" alt="Logo" className="chat-welcome-logo" />
          <h2 className="chat-welcome-title">How can I help you today?</h2>
        </div>
      </div>
    );
  }

  return (
    <div className="chat-messages" id="chatMessages">
      {messages.map((message, index) => (
        <div key={index} className={`message ${message.role}-message`}>
          <div className="message-content">
            <ReactMarkdown remarkPlugins={[remarkGfm]}>
              {message.content}
            </ReactMarkdown>
          </div>
          <MessageActions message={message} messageIndex={index} />
        </div>
      ))}
      <div ref={messagesEndRef} />
    </div>
  );
}

export default ChatMessages;
