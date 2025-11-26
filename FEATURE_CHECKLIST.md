# Complete Feature Checklist for React Migration

## ✅ **CRITICAL**: ALL Features Must Be Preserved During Migration

---

## 1. **Setup Wizard (6-Page Onboarding)**

### Page 1: Welcome
- [ ] Logo display
- [ ] Welcome title and description
- [ ] Get Started button
- [ ] Page dots navigation (6 dots)

### Page 2: Features Overview
- [ ] Multi-Model Chat feature card
- [ ] Document Analysis feature card
- [ ] Web Search feature card
- [ ] Voice Support feature card
- [ ] Back/Continue navigation

### Page 3: OpenAI API Key Setup
- [ ] OpenAI logo/icon
- [ ] API key input field
- [ ] Show/Hide password toggle (eye icon)
- [ ] Link to OpenAI platform
- [ ] Skip button with warning
- [ ] Back/Continue buttons
- [ ] API key validation

### Page 4: Google Gemini API Key Setup
- [ ] Gemini logo with gradient
- [ ] API key input field
- [ ] Show/Hide password toggle
- [ ] Link to Google AI Studio
- [ ] Skip button with warning
- [ ] Back/Continue buttons
- [ ] API key validation

### Page 5: Local LLM (llama.cpp) Setup
- [ ] llama.cpp logo
- [ ] Installation status checking
- [ ] Terminal output display
- [ ] Install llama.cpp button
- [ ] Real-time installation progress (SSE)
- [ ] Skip button
- [ ] Back button
- [ ] Installation state management

### Page 6: Model Download
- [ ] GPT-OSS-20B model card (~13.8 GB)
- [ ] Qwen3-8B model card (~5.2 GB)
- [ ] Download button for each model
- [ ] Progress bar with percentage
- [ ] Download speed indicator
- [ ] Model status indicators
- [ ] Terminal output for downloads
- [ ] Skip button
- [ ] Finish Setup button
- [ ] Real-time download progress (SSE)

### Setup Wizard - Additional Features
- [ ] Skip warning modal with confirmation
- [ ] Welcome animation after completion
- [ ] Setup completion state persistence
- [ ] Mini model download wizard (triggered from chat)
- [ ] API key storage to backend
- [ ] Setup status check on load

---

## 2. **Chat Interface**

### Header
- [ ] Model provider dropdown selector
- [ ] Center logo
- [ ] Status indicator (dot + text)
- [ ] Theme toggle (sun/moon icons)
- [ ] Clear chat button
- [ ] Responsive header layout

### Chat Messages Area
- [ ] Welcome screen (empty state with logo)
- [ ] User message bubbles
- [ ] Assistant message bubbles
- [ ] Markdown rendering in messages
- [ ] Code syntax highlighting
- [ ] Message timestamps
- [ ] Streaming message animation
- [ ] Tool usage indicators
- [ ] Auto-scroll to bottom
- [ ] Copy message button
- [ ] Regenerate response button
- [ ] Voice playback button (TTS)

### Input Area
- [ ] Auto-resizing textarea
- [ ] Placeholder text
- [ ] Send button
- [ ] Web search toggle button
- [ ] File upload button (documents)
- [ ] Image upload button
- [ ] Camera button
- [ ] Response style dropdown
- [ ] Prevent zoom on iOS double-tap
- [ ] Enter to send, Shift+Enter for newline
- [ ] Loading state during message send

---

## 3. **Session Management**

### Sidebar
- [ ] New chat button
- [ ] Session list display
- [ ] Session title (auto-generated from first message)
- [ ] Session timestamp (relative: "2m ago", "5h ago", etc.)
- [ ] Active session highlighting
- [ ] Delete session button per session
- [ ] Delete confirmation
- [ ] Empty state message
- [ ] Sidebar toggle button (mobile)
- [ ] Sidebar overlay (mobile backdrop)
- [ ] Responsive sidebar behavior

### Session Operations
- [ ] Create new session
- [ ] Load existing session with messages
- [ ] Delete session
- [ ] Switch between sessions
- [ ] Auto-create session on first message
- [ ] Session title generation (30 char limit)
- [ ] Update session on new message
- [ ] Persist current session ID
- [ ] Load messages when switching sessions

---

## 4. **Document Upload & Management**

- [ ] File input (PDF, TXT, DOCX, DOC)
- [ ] File selection dialog
- [ ] Upload progress indicator
- [ ] Document list display
- [ ] Document chips with name and icon
- [ ] Remove document button (per document)
- [ ] Document area show/hide
- [ ] Upload to backend API
- [ ] Load session documents on session switch
- [ ] Document metadata (filename, size)
- [ ] Multiple document support
- [ ] Document persistence per session

---

## 5. **Image & Camera Features**

### Image Upload
- [ ] Image file input (accept image/*)
- [ ] Image selection from device
- [ ] Image preview area
- [ ] Preview thumbnail
- [ ] Remove image button
- [ ] Image upload to backend
- [ ] Image preview area show/hide

### Camera Capture
- [ ] Camera modal overlay
- [ ] Camera modal backdrop
- [ ] Live camera preview (video element)
- [ ] Camera permission request
- [ ] Camera error handling
- [ ] Camera access denied message
- [ ] Switch camera button (front/back)
- [ ] Capture button
- [ ] Retake button
- [ ] Use photo button
- [ ] Close modal button
- [ ] Canvas for photo capture
- [ ] Captured image preview
- [ ] Multiple camera device support
- [ ] iOS/iPad camera optimization

---

## 6. **Google Maps Integration**

- [ ] Maps popup overlay
- [ ] Maps popup backdrop
- [ ] Maps popup header with title
- [ ] Close maps button
- [ ] Maps widget container
- [ ] Loading spinner for maps
- [ ] Maps iframe embedding
- [ ] Close popup on backdrop click
- [ ] Maps integration triggered from messages

---

## 7. **Model Provider & Configuration**

### Model Provider Selection
- [ ] Fetch available model providers from API
- [ ] Dropdown populated dynamically
- [ ] OpenAI models (GPT-4, GPT-3.5, etc.)
- [ ] Google Gemini models
- [ ] Local llama.cpp models
- [ ] Model provider persistence
- [ ] Change model mid-conversation

### Response Style
- [ ] Response style dropdown
- [ ] Fetch available styles from API
- [ ] Normal, Detailed, Concise, Creative modes
- [ ] Style toggle button
- [ ] Style persistence
- [ ] Apply style to messages

---

## 8. **Web Search**

- [ ] Web search toggle button
- [ ] Search enabled indicator
- [ ] Send message with search flag
- [ ] Search results in message
- [ ] Search status in UI

---

## 9. **Voice & TTS**

- [ ] Text-to-speech for messages
- [ ] Voice playback button per message
- [ ] TTS API integration
- [ ] Audio playback controls
- [ ] Voice status indicator

---

## 10. **Theme System**

- [ ] Light theme
- [ ] Dark theme
- [ ] Theme toggle button
- [ ] Theme persistence (localStorage)
- [ ] Theme applied to entire app
- [ ] Smooth theme transitions
- [ ] data-theme attribute on HTML

---

## 11. **Health Check & Status**

- [ ] Server health check on load
- [ ] Health check API call
- [ ] Online/offline detection
- [ ] Status indicator updates
- [ ] Auto-reconnect on connection restore
- [ ] Network status events

---

## 12. **Error Handling**

- [ ] Error toast/notification
- [ ] Success notifications
- [ ] API error handling
- [ ] Network error handling
- [ ] Retry logic with exponential backoff
- [ ] User-friendly error messages
- [ ] Form validation errors

---

## 13. **Responsive Design**

- [ ] Mobile layout (< 768px)
- [ ] Tablet layout (768px - 1024px)
- [ ] Desktop layout (> 1024px)
- [ ] Sidebar responsive behavior
- [ ] Mobile sidebar overlay
- [ ] Touch-friendly buttons
- [ ] Mobile input optimization
- [ ] iOS viewport handling
- [ ] iPad optimization

---

## 14. **API Endpoints (All Must Be Called)**

### Sessions
- [ ] `POST /api/sessions` - Create session
- [ ] `GET /api/sessions` - List sessions
- [ ] `GET /api/sessions/:id` - Get session
- [ ] `DELETE /api/sessions/:id` - Delete session

### Messages
- [ ] `POST /api/messages` - Save message
- [ ] `GET /api/messages/:sessionId` - Get messages
- [ ] `POST /api/chat` - Send chat message (SSE)

### Documents
- [ ] `POST /api/documents/upload` - Upload document
- [ ] `GET /api/documents/:sessionId` - Get session documents
- [ ] `DELETE /api/documents/:id` - Delete document

### Models
- [ ] `GET /api/models/providers` - Get model providers
- [ ] `GET /api/models/styles` - Get response styles

### Setup
- [ ] `GET /api/setup/status` - Check setup status
- [ ] `POST /api/setup/keys` - Save API keys
- [ ] `POST /api/setup/llama/install` - Install llama.cpp (SSE)
- [ ] `POST /api/setup/models/download` - Download model (SSE)
- [ ] `GET /api/setup/models/status` - Check model status

### Health
- [ ] `GET /api/health` - Health check

### Voice
- [ ] `POST /api/voice/tts` - Text-to-speech

### Images
- [ ] `POST /api/image/upload` - Upload image
- [ ] `POST /api/image/analyze` - Analyze image

### Config
- [ ] `GET /api/config` - Get config
- [ ] `PUT /api/config` - Update config

### Gmail Auth (if applicable)
- [ ] `/auth/gmail` - Gmail auth
- [ ] `/auth/gmail/callback` - OAuth callback

---

## 15. **Real-Time Features (Server-Sent Events)**

- [ ] Chat message streaming (SSE)
- [ ] llama.cpp installation progress (SSE)
- [ ] Model download progress (SSE)
- [ ] EventSource connection management
- [ ] Reconnection on disconnect
- [ ] Event stream parsing

---

## 16. **Additional Features**

### Modular JavaScript Features
- [ ] All features from `js/modules/api.js`
- [ ] All features from `js/modules/ui.js`
- [ ] All features from `js/modules/messaging.js`
- [ ] All features from `js/modules/session.js`
- [ ] All features from `js/modules/document.js`
- [ ] All features from `js/modules/maps.js`

### CSS & Styling (9 CSS Files)
- [ ] base.css - Base styles, CSS variables
- [ ] main.css - Main layout
- [ ] chat.css - Chat interface styles
- [ ] sidebar.css - Sidebar styles
- [ ] components.css - Button, input components
- [ ] documents.css - Document upload styles
- [ ] setup.css - Setup wizard styles
- [ ] responsive.css - Media queries
- [ ] maps-popup.css - Maps popup styles

### Assets
- [ ] Logo images (PNG)
- [ ] llama.cpp logo
- [ ] Favicon
- [ ] All SVG icons

---

## 17. **State Management Requirements**

- [ ] Current session ID
- [ ] Session list
- [ ] Current messages
- [ ] Conversation history
- [ ] Request in progress state
- [ ] Message count
- [ ] Online/offline status
- [ ] Selected model provider
- [ ] Selected response style
- [ ] Theme preference
- [ ] Uploaded documents
- [ ] Uploaded images
- [ ] Setup completion status
- [ ] API keys (stored in backend)

---

## 18. **Browser Compatibility**

- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (iOS + macOS)
- [ ] iPad specific optimizations
- [ ] Mobile Safari optimizations
- [ ] Camera API compatibility

---

## 19. **Performance Requirements**

- [ ] Code splitting for vendor libraries
- [ ] Lazy loading for routes/components
- [ ] Image optimization
- [ ] Bundle size optimization
- [ ] Fast initial load time
- [ ] Smooth animations
- [ ] Efficient re-renders

---

## Total Feature Count: **200+ Individual Features**

### Migration Status: ⏳ **NOT STARTED**
### Target: ✅ **100% Feature Parity**

---

**IMPORTANT NOTES:**
1. Every checkbox must be ✅ before migration is complete
2. Test each feature manually after migration
3. Compare side-by-side with original app
4. Document any deviations or improvements
5. Get user approval before removing ANY feature

