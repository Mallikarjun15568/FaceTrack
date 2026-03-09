"""
Simple Browser TTS Announcement System
Zero setup, instant playback using browser's built-in speech synthesis
"""

from utils.logger import logger

class SimpleAudioService:
    """
    Simple browser TTS for kiosk announcements.
    Zero dependencies, zero setup, works instantly.
    """
    
    def __init__(self, app=None):
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        logger.info("✅ Browser TTS announcements enabled")
    
    def get_browser_tts_config(self, employee_name, status):
        """
        Generate optimized browser TTS config.
        Uses browser's built-in speech synthesis.
        """
        messages = {
            'check-in': f"Welcome {employee_name}",
            'check-out': f"Goodbye {employee_name}",
            'already': f"{employee_name}, already marked"
        }
        
        return {
            'text': messages.get(status, f"Welcome {employee_name}"),
            'lang': 'en-IN',
            'rate': 0.9,  # Slightly slower for clarity
            'pitch': 1.0,
            'volume': 1.0,
            # Preferred voices (client will try to find these)
            'preferredVoices': [
                'Google UK English Male',
                'Microsoft Heera - English (India)',
                'Google हिन्दी'
            ]
        }


# Global instance
simple_audio = SimpleAudioService()
