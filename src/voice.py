"""Text-to-speech module using Google Gemini 2.5 Flash TTS."""
import io
import os
import wave
from typing import Optional
from google import genai
from google.genai import types
from src.logging_config import get_logger
from src.config import Config
from src.utils.token_tracker import get_request_tracker

logger = get_logger("chatbot.voice")


class VoiceGenerator:
    """Generate speech from text using Google Gemini 2.5 Flash TTS."""

    def __init__(self):
        """Initialize the voice generator with Google GenAI client."""
        # Check for Vertex AI or API Key authentication
        gcp_project = os.getenv("GCP_PROJECT_ID")
        gcp_location = os.getenv("GCP_LOCATION", "us-east5")
        api_key = os.getenv("GEMINI_API_KEY")

        if gcp_project:
            # Use Vertex AI authentication (preferred - no rate limits)
            logger.info(f"[VOICE] Initializing with Vertex AI project: {gcp_project}")
            self.client = genai.Client(
                vertexai=True,
                project=gcp_project,
                location=gcp_location
            )
        elif api_key:
            # Use API Key authentication (fallback)
            logger.info("[VOICE] Initializing with Gemini API Key")
            self.client = genai.Client(api_key=api_key)
        else:
            raise ValueError(
                "Neither GCP_PROJECT_ID nor GEMINI_API_KEY found. "
                "Please set one in your .env file."
            )

        # Fetch TTS configuration from config
        self.model = Config.GEMINI_TTS_MODEL
        self.voice = Config.GEMINI_TTS_VOICE

        logger.info(f"[VOICE] Initialized: model={self.model}, voice={self.voice}")

    def generate_speech(
        self,
        text: str,
        response_format: str = "wav"
    ) -> Optional[bytes]:
        """
        Generate speech from text using Gemini 2.5 Flash TTS.

        Args:
            text: The text to convert to speech
            response_format: Audio format (wav, mp3, etc.) - currently supports wav/pcm

        Returns:
            Audio data as bytes, or None if generation fails
        """
        try:
            logger.info("=" * 60)
            logger.info(f"[VOICE] Generating speech for text: {text[:100]}...")
            logger.info(f"[VOICE] Using model: {self.model}, voice: {self.voice}")

            # Configure speech parameters for Gemini TTS
            speech_config = types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=self.voice
                    )
                )
            )

            # Generate audio using Gemini TTS
            response = self.client.models.generate_content(
                model=self.model,
                contents=text,
                config=types.GenerateContentConfig(
                    response_modalities=["AUDIO"],
                    speech_config=speech_config
                )
            )

            logger.info('[VOICE] Received response from Gemini TTS API')
            print('[VOICE] Received Audio response from Gemini TTS API')

            # Extract audio data from response
            audio_data = None
            if response.candidates and response.candidates[0].content.parts:
                part = response.candidates[0].content.parts[0]
                if part.inline_data and part.inline_data.data:
                    audio_data = part.inline_data.data
                    logger.info(f"[VOICE] Got raw audio data: {len(audio_data)} bytes")

            if audio_data is None:
                logger.error("[VOICE] No audio data in response")
                return None

            # Convert to requested format
            audio_bytes = self._convert_audio(audio_data, response_format)

            logger.info(f"[VOICE] Successfully generated {len(audio_bytes)} bytes of audio data")

            # Track TTS usage for cost calculation
            tracker = get_request_tracker()
            tracker.add_tts_usage(text, self.model)
            logger.info("=" * 60)
            logger.info(f"TTS USAGE")
            logger.info(f"Model: {self.model}")
            logger.info(f"Characters: {len(text):,}")
            logger.info("=" * 60)

            return audio_bytes

        except Exception as e:
            logger.error(f"[VOICE] ERROR generating speech: {type(e).__name__}: {str(e)}")
            logger.exception("[VOICE] Full traceback:")
            print(f'[VOICE] ERROR: {e}')
            return None

    def _convert_audio(self, audio_data: bytes, target_format: str) -> bytes:
        """
        Convert raw PCM audio data to the requested format.

        Gemini TTS returns raw PCM data at 24kHz, 16-bit, mono.

        Args:
            audio_data: Raw PCM audio bytes from Gemini
            target_format: Target format (wav, pcm, etc.)

        Returns:
            Audio data in the requested format
        """
        if target_format == "pcm":
            # Return raw PCM data as-is
            return audio_data

        if target_format in ["wav", "mp3", "opus", "aac", "flac"]:
            # Wrap PCM data in WAV container
            # Gemini TTS outputs: 24kHz, 16-bit, mono PCM
            wav_buffer = io.BytesIO()
            with wave.open(wav_buffer, 'wb') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit = 2 bytes
                wav_file.setframerate(24000)  # 24kHz
                wav_file.writeframes(audio_data)

            return wav_buffer.getvalue()

        # Default: return as WAV
        logger.warning(f"[VOICE] Unknown format '{target_format}', returning WAV")
        return self._convert_audio(audio_data, "wav")


# Singleton instance
_voice_generator = None


def get_voice_generator() -> VoiceGenerator:
    """Get or create the voice generator instance."""
    global _voice_generator
    if _voice_generator is None:
        _voice_generator = VoiceGenerator()
    return _voice_generator
