import { useState } from 'react';

function DeleteConfirmDialog({ isOpen, onConfirm, onCancel, title = "Delete this chat?" }) {
    if (!isOpen) return null;

    return (
        <div className="delete-confirm-overlay" onClick={onCancel}>
            <div className="delete-confirm-dialog" onClick={(e) => e.stopPropagation()}>
                <div className="delete-confirm-header">
                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
                        <circle cx="12" cy="12" r="10"></circle>
                        <line x1="12" y1="8" x2="12" y2="12"></line>
                        <line x1="12" y1="16" x2="12.01" y2="16"></line>
                    </svg>
                </div>
                <h3 className="delete-confirm-title">{title}</h3>
                <p className="delete-confirm-message">This action cannot be undone.</p>
                <div className="delete-confirm-actions">
                    <button className="delete-confirm-btn cancel" onClick={onCancel}>
                        Cancel
                    </button>
                    <button className="delete-confirm-btn confirm" onClick={onConfirm}>
                        Delete
                    </button>
                </div>
            </div>
        </div>
    );
}

export default DeleteConfirmDialog;
