import { useRef } from 'react';
import useStore from '../../store/useStore';
import ResponseStyleSelector from './ResponseStyleSelector';

function InputActions({ onDocumentUpload, onImageUpload, onCameraClick }) {
    const fileInputRef = useRef(null);
    const imageInputRef = useRef(null);

    const {
        documents,
        currentImage,
        webSearchEnabled,
        toggleWebSearch
    } = useStore();

    const handleDocumentClick = () => {
        fileInputRef.current?.click();
    };

    const handleImageClick = () => {
        imageInputRef.current?.click();
    };

    const handleFileChange = (e) => {
        const file = e.target.files?.[0];
        if (file && onDocumentUpload) {
            onDocumentUpload(file);
        }
    };

    const handleImageChange = (e) => {
        const file = e.target.files?.[0];
        if (file && onImageUpload) {
            onImageUpload(file);
        }
    };

    return (
        <div className="input-actions">
            {/* Hidden file inputs */}
            <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,.txt,.doc,.docx"
                style={{ display: 'none' }}
                onChange={handleFileChange}
            />
            <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleImageChange}
            />

            {/* Response Style Selector (Settings) */}
            <ResponseStyleSelector />

            {/* Document upload button */}
            <button
                className={`attach-button ${documents.length > 0 ? 'has-document' : ''}`}
                title="Upload document"
                onClick={handleDocumentClick}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19a4 4 0 015.66 5.66l-9.2 9.19a2 2 0 01-2.83-2.83l8.49-8.48"></path>
                </svg>
            </button>

            {/* Image upload button */}
            <button
                className={`image-upload-button ${currentImage ? 'has-image' : ''}`}
                title="Upload image"
                onClick={handleImageClick}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect>
                    <circle cx="8.5" cy="8.5" r="1.5"></circle>
                    <polyline points="21 15 16 10 5 21"></polyline>
                </svg>
            </button>

            {/* Camera button */}
            <button
                className="camera-button"
                title="Take photo"
                onClick={onCameraClick}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M23 19a2 2 0 01-2 2H3a2 2 0 01-2-2V8a2 2 0 012-2h4l2-3h6l2 3h4a2 2 0 012 2z"></path>
                    <circle cx="12" cy="13" r="4"></circle>
                </svg>
            </button>

            {/* Web search toggle button */}
            <button
                className={`search-button ${webSearchEnabled ? 'active' : ''}`}
                title={webSearchEnabled ? 'Web search enabled' : 'Enable web search'}
                onClick={toggleWebSearch}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="11" cy="11" r="8"></circle>
                    <path d="M21 21l-4.35-4.35"></path>
                </svg>
            </button>
        </div>
    );
}

export default InputActions;
