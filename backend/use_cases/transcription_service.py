class TranscriptionService:
    def __init__(self, whisper_framework):
        self.whisper = whisper_framework
        
    async def transcribe(self, audio_path: str) -> tuple[str, str]:
        """Returns (transcription, error)"""
        try:
            # Call abstract framework method
            text = await self.whisper.transcribe_audio(audio_path)
            return text, None
        except Exception as e:
            return "", str(e)
