import { useState } from 'react';
import { deleteMessage } from '../../services/api';
import useStore from '../../store/useStore';
import DeleteConfirmDialog from '../common/DeleteConfirmDialog';

function MessageActions({ message, messageIndex }) {
    const [isDeleting, setIsDeleting] = useState(false);
    const [showConfirm, setShowConfirm] = useState(false);
    const { currentSessionId, messages, setMessages } = useStore();

    const handleDeleteClick = () => {
        setShowConfirm(true);
    };

    const handleConfirmDelete = async () => {
        setIsDeleting(true);
        try {
            // If message has an ID, delete from backend
            if (message.id) {
                await deleteMessage(currentSessionId, message.id);
            }

            // Remove from local state
            const newMessages = messages.filter((_, index) => index !== messageIndex);
            setMessages(newMessages);
        } catch (error) {
            console.error('Failed to delete message:', error);
            // We can add a toast notification here later
        } finally {
            setIsDeleting(false);
            setShowConfirm(false);
        }
    };

    const handleCancelDelete = () => {
        setShowConfirm(false);
    };

    return (
        <>
            <div className="message-actions">
                <button
                    className="message-delete-btn"
                    title="Delete message"
                    onClick={handleDeleteClick}
                    disabled={isDeleting}
                >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M3 6h18M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a2 2 0 012-2h4a2 2 0 012 2v2M10 11v6M14 11v6"></path>
                    </svg>
                </button>
            </div>

            <DeleteConfirmDialog
                isOpen={showConfirm}
                onConfirm={handleConfirmDelete}
                onCancel={handleCancelDelete}
                title="Delete this message?"
            />
        </>
    );
}

export default MessageActions;
