import { useState, useRef, useEffect } from 'react';
import useStore from '../../store/useStore';

function ResponseStyleSelector() {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef(null);
    const { responseStyle, setResponseStyle, responseStyles } = useStore();

    // Close dropdown when clicking outside
    useEffect(() => {
        const handleClickOutside = (event) => {
            if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
                setIsOpen(false);
            }
        };

        document.addEventListener('mousedown', handleClickOutside);
        return () => {
            document.removeEventListener('mousedown', handleClickOutside);
        };
    }, []);

    const handleStyleSelect = (style) => {
        setResponseStyle(style);
        setIsOpen(false);
    };

    return (
        <div className="style-toggle-wrapper" ref={dropdownRef}>
            <button
                className={`style-toggle-button ${isOpen ? 'active' : ''}`}
                title={`Response Style: ${responseStyle}`}
                onClick={() => setIsOpen(!isOpen)}
            >
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <path d="M12 20a8 8 0 1 0 0-16 8 8 0 0 0 0 16z"></path>
                    <line x1="12" y1="14" x2="12" y2="6"></line>
                    <line x1="12" y1="18" x2="12.01" y2="18"></line>
                </svg>
            </button>

            <div className={`style-dropdown ${isOpen ? 'show' : ''}`}>
                <div className="style-dropdown-header">Response Style</div>
                {responseStyles.length > 0 ? (
                    responseStyles.map((style) => (
                        <div
                            key={style}
                            className={`style-option ${responseStyle === style ? 'selected' : ''}`}
                            onClick={() => handleStyleSelect(style)}
                        >
                            {style}
                            {responseStyle === style && (
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            )}
                        </div>
                    ))
                ) : (
                    // Fallback options if API hasn't loaded styles yet
                    ['Normal', 'Concise', 'Creative', 'Formal'].map((style) => (
                        <div
                            key={style}
                            className={`style-option ${responseStyle === style ? 'selected' : ''}`}
                            onClick={() => handleStyleSelect(style)}
                        >
                            {style}
                            {responseStyle === style && (
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="20 6 9 17 4 12"></polyline>
                                </svg>
                            )}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}

export default ResponseStyleSelector;
