"""Audio management for TTS and sound effects."""

import io
import os
import threading
from typing import Optional, Dict

import numpy as np
import pygame
from openai import OpenAI

from .config import (
    AUDIO_SAMPLE_RATE,
    WALKING_SOUND_FREQUENCY,
    WALKING_SOUND_DURATION,
    APPLE_CONNECT_COMMAND,
    FLOODGATE_BASE_URL,
)


def setup_openai_client() -> Optional[OpenAI]:
    """Set up OpenAI client with Apple internal authentication."""
    try:
        print("Attempting to authenticate with Apple Floodgate...")
        token_output = os.popen(APPLE_CONNECT_COMMAND).read()
        
        if not token_output or token_output.strip() == "":
            print("Warning: No token received from appleconnect command")
            print("TTS will be disabled. Animation will run without audio dialogue.")
            return None
            
        token = token_output.split()[-1]
        
        if len(token) < 10:  # Basic sanity check
            print(f"Warning: Token appears invalid (length: {len(token)})")
            print("TTS will be disabled. Animation will run without audio dialogue.")
            return None
            
        client = OpenAI(api_key=token)
        client.base_url = FLOODGATE_BASE_URL
        print("✓ Successfully authenticated with Apple Floodgate")
        return client
    except Exception as e:
        print(f"Warning: Could not set up OpenAI client: {e}")
        print("TTS will be disabled. Animation will run without audio dialogue.")
        return None


class AudioManager:
    """Manages audio generation and playback for the animation."""

    def __init__(self):
        """Initialize the audio manager."""
        self.audio_cache: Dict[str, pygame.mixer.Sound] = {}
        self.current_sound: Optional[pygame.mixer.Sound] = None
        self.openai_client = setup_openai_client()

    def generate_tts_audio(
        self, text: str, voice: str = "alloy", filename: Optional[str] = None
    ) -> Optional[pygame.mixer.Sound]:
        """
        Generate TTS audio using OpenAI API.

        Args:
            text: The text to convert to speech
            voice: The voice to use (alloy, echo, fable, onyx, nova, shimmer)
            filename: Optional filename to save the audio

        Returns:
            pygame.mixer.Sound object or None if generation fails
        """
        if not self.openai_client:
            # Silently skip if client not available (already warned during init)
            return None

        try:
            # Check cache first
            cache_key = f"{text}_{voice}"
            if cache_key in self.audio_cache:
                return self.audio_cache[cache_key]

            response = self.openai_client.audio.speech.create(
                model="tts-1", voice=voice, input=text
            )

            # Convert to pygame sound
            audio_data = response.content
            audio_file = io.BytesIO(audio_data)
            sound = pygame.mixer.Sound(audio_file)

            # Cache the sound
            self.audio_cache[cache_key] = sound

            # Optionally save to file
            if filename:
                with open(filename, "wb") as f:
                    f.write(audio_data)

            print(f"✓ Generated TTS for: {text[:50]}...")
            return sound

        except Exception as e:
            # Only print detailed error on first failure
            if not hasattr(self, '_tts_error_shown'):
                print(f"\n⚠️  TTS Error: {e}")
                print("This is likely due to:")
                print("  1. Not being on Apple's internal network")
                print("  2. Expired authentication token")
                print("  3. Network connectivity issues")
                print("\nAnimation will continue without dialogue audio.\n")
                self._tts_error_shown = True
            return None

    def load_walking_sound(self, filepath: str = "assets/walking.wav") -> Optional[pygame.mixer.Sound]:
        """
        Load walking sound from file, with fallback to generated sound.

        Args:
            filepath: Path to the walking sound file

        Returns:
            pygame.mixer.Sound object or None if loading fails
        """
        try:
            # Try to load from file first
            sound = pygame.mixer.Sound(filepath)
            return sound
        except (FileNotFoundError, pygame.error) as e:
            print(f"Could not load walking sound from {filepath}: {e}")
            print("Falling back to generated walking sound")
            return self._generate_walking_sound()

    def _generate_walking_sound(self) -> Optional[pygame.mixer.Sound]:
        """
        Generate a simple walking sound effect as fallback.

        Returns:
            pygame.mixer.Sound object or None if generation fails
        """
        try:
            frames = int(WALKING_SOUND_DURATION * AUDIO_SAMPLE_RATE)

            # Generate a simple click sound for footsteps
            t = np.linspace(0, WALKING_SOUND_DURATION, frames)
            # Decaying sine wave for a thump sound
            wave = np.sin(WALKING_SOUND_FREQUENCY * 2 * np.pi * t) * np.exp(-t * 20)

            # Convert to pygame sound format
            wave = (wave * 32767).astype(np.int16)
            stereo_wave = np.column_stack((wave, wave))
            # Ensure C-contiguous array
            stereo_wave = np.ascontiguousarray(stereo_wave)
            sound = pygame.sndarray.make_sound(stereo_wave)

            return sound
        except ImportError:
            print("NumPy not available, walking sound disabled")
            return None
        except Exception as e:
            print(f"Error generating walking sound: {e}")
            return None

    def play_sound(self, sound: Optional[pygame.mixer.Sound]) -> None:
        """
        Play a sound once.

        Args:
            sound: The pygame.mixer.Sound to play
        """
        if sound:
            try:
                self.current_sound = sound
                sound.play()
            except Exception as e:
                print(f"Error playing sound: {e}")

    def play_looping_sound(self, sound: Optional[pygame.mixer.Sound]) -> None:
        """
        Play a sound in a loop.

        Args:
            sound: The pygame.mixer.Sound to play
        """
        if sound:
            try:
                self.current_sound = sound
                sound.play(loops=-1)  # -1 means loop indefinitely
            except Exception as e:
                print(f"Error playing looping sound: {e}")

    def stop_current_sound(self) -> None:
        """Stop currently playing sound."""
        if self.current_sound:
            self.current_sound.stop()
            self.current_sound = None
    
    def is_sound_playing(self, sound: Optional[pygame.mixer.Sound]) -> bool:
        """
        Check if a specific sound is currently playing.
        
        Args:
            sound: The sound to check
            
        Returns:
            True if the sound is playing, False otherwise
        """
        if sound and self.current_sound == sound:
            return sound.get_num_channels() > 0
        return False

    def preload_dialogue(
        self, dialogues: list[tuple[str, str, str]]
    ) -> Dict[str, pygame.mixer.Sound]:
        """
        Preload all dialogue audio in background.

        Args:
            dialogues: List of (text, speaker, voice) tuples

        Returns:
            Dictionary mapping text to Sound objects
        """
        dialogue_audio = {}

        def generate_all():
            if not self.openai_client:
                print("\nℹ️  TTS not available - animation will run silently")
                return
                
            print("\nGenerating dialogue audio...")
            for text, _, voice in dialogues:
                sound = self.generate_tts_audio(text, voice)
                if sound:
                    dialogue_audio[text] = sound
            
            if dialogue_audio:
                print(f"✓ Successfully generated {len(dialogue_audio)} dialogue clips\n")

        # Start audio generation in background
        audio_thread = threading.Thread(target=generate_all)
        audio_thread.daemon = True
        audio_thread.start()

        return dialogue_audio