import { useState, useRef, useEffect } from 'react';
import useStore from '../../store/useStore';

function CameraModal({ isOpen, onClose }) {
    const [stream, setStream] = useState(null);
    const [capturedImage, setCapturedImage] = useState(null);
    const [error, setError] = useState(null);
    const [facingMode, setFacingMode] = useState('user'); // 'user' or 'environment'
    const videoRef = useRef(null);
    const canvasRef = useRef(null);
    const { setCurrentImage } = useStore();

    useEffect(() => {
        if (isOpen) {
            startCamera();
        } else {
            stopCamera();
            setCapturedImage(null);
            setError(null);
        }

        return () => {
            stopCamera();
        };
    }, [isOpen, facingMode]);

    const startCamera = async () => {
        try {
            setError(null);
            const mediaStream = await navigator.mediaDevices.getUserMedia({
                video: { facingMode },
                audio: false
            });
            setStream(mediaStream);
            if (videoRef.current) {
                videoRef.current.srcObject = mediaStream;
            }
        } catch (err) {
            console.error('Camera error:', err);
            setError('Unable to access camera. Please check permissions.');
        }
    };

    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            setStream(null);
        }
    };

    const capturePhoto = () => {
        if (!videoRef.current || !canvasRef.current) return;

        const video = videoRef.current;
        const canvas = canvasRef.current;
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        const imageDataUrl = canvas.toDataURL('image/jpeg', 0.9);
        setCapturedImage(imageDataUrl);
        stopCamera();
    };

    const retakePhoto = () => {
        setCapturedImage(null);
        startCamera();
    };

    const switchCamera = () => {
        setFacingMode(prev => prev === 'user' ? 'environment' : 'user');
    };

    const usePhoto = () => {
        if (capturedImage) {
            setCurrentImage(capturedImage);
            onClose();
        }
    };

    const handleBackdropClick = (e) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="camera-modal" onClick={handleBackdropClick}>
            <div className="camera-modal-backdrop"></div>
            <div className="camera-modal-content">
                <div className="camera-modal-header">
                    <h3>{capturedImage ? 'Photo Captured' : 'Take Photo'}</h3>
                    <button className="camera-modal-close" onClick={onClose}>
                        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <line x1="18" y1="6" x2="6" y2="18"></line>
                            <line x1="6" y1="6" x2="18" y2="18"></line>
                        </svg>
                    </button>
                </div>

                <div className="camera-modal-body">
                    <div className="camera-view-container">
                        {error ? (
                            <div className="camera-error">
                                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <circle cx="12" cy="12" r="10"></circle>
                                    <line x1="12" y1="8" x2="12" y2="12"></line>
                                    <line x1="12" y1="16" x2="12.01" y2="16"></line>
                                </svg>
                                <p>{error}</p>
                            </div>
                        ) : capturedImage ? (
                            <img src={capturedImage} alt="Captured" />
                        ) : (
                            <video ref={videoRef} autoPlay playsInline muted />
                        )}
                    </div>
                    <canvas ref={canvasRef} style={{ display: 'none' }} />
                </div>

                <div className="camera-modal-footer">
                    {capturedImage ? (
                        <>
                            <button className="camera-retake-btn" onClick={retakePhoto} title="Retake">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <polyline points="1 4 1 10 7 10"></polyline>
                                    <polyline points="23 20 23 14 17 14"></polyline>
                                    <path d="M20.49 9A9 9 0 0 0 5.64 5.64L1 10m22 4l-4.64 4.36A9 9 0 0 1 3.51 15"></path>
                                </svg>
                            </button>
                            <button className="camera-use-btn" onClick={usePhoto}>
                                Use Photo
                            </button>
                        </>
                    ) : (
                        <>
                            <button className="camera-switch-btn" onClick={switchCamera} title="Switch camera">
                                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                    <path d="M17 10l5 5-5 5"></path>
                                    <path d="M7 14L2 9l5-5"></path>
                                    <path d="M22 9H2"></path>
                                    <path d="M2 15h20"></path>
                                </svg>
                            </button>
                            <button className="camera-capture-btn" onClick={capturePhoto} title="Capture">
                                <div className="capture-btn-inner"></div>
                            </button>
                            <div style={{ width: '48px' }}></div> {/* Spacer for centering */}
                        </>
                    )}
                </div>
            </div>
        </div>
    );
}

export default CameraModal;
