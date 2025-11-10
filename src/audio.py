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

    def load_dialogue_file(self, filepath: str) -> Optional[pygame.mixer.Sound]:
        """
        Load a dialogue audio file.

        Args:
            filepath: Path to the audio file

        Returns:
            pygame.mixer.Sound object or None if loading fails
        """
        try:
            sound = pygame.mixer.Sound(filepath)
            return sound
        except (FileNotFoundError, pygame.error) as e:
            print(f"Could not load dialogue from {filepath}: {e}")
            return None

    def preload_dialogue(
        self, dialogues: list[tuple[str, str, str]]
    ) -> tuple[Dict[str, pygame.mixer.Sound], Dict[str, int]]:
        """
        Preload all dialogue audio from files.

        Args:
            dialogues: List of (text, speaker, voice) tuples

        Returns:
            Tuple of (Dictionary mapping text to Sound objects, Dictionary mapping text to duration in ms)
        """
        dialogue_audio = {}
        dialogue_durations = {}
        
        # Mapping of dialogue text to file paths
        dialogue_files = {
            "WATCH IT!_char1": "assets/01_01_watch_it.wav",
            "WATCH IT!_char2": "assets/01_02_watch_it.wav",
            "Just kidding, running into people is fun!": "assets/02_01_just_kidding.wav",
            "Hey ya!": "assets/03_02_hey_ya.wav",
            "Okay I have to go to work": "assets/04_01_go_to_work.wav",
            "I don't care": "assets/05_02_i_dont_care.wav",
        }
        
        print("\nLoading dialogue audio files...")
        for text, speaker, _ in dialogues:
            if text == "WATCH IT!":
                # Load both character versions for simultaneous playback
                char1_sound = self.load_dialogue_file(dialogue_files["WATCH IT!_char1"])
                char2_sound = self.load_dialogue_file(dialogue_files["WATCH IT!_char2"])
                if char1_sound and char2_sound:
                    # Store both sounds as a tuple
                    dialogue_audio[text] = (char1_sound, char2_sound)
                    # Use the longer duration of the two
                    duration = max(
                        int(char1_sound.get_length() * 1000),
                        int(char2_sound.get_length() * 1000)
                    )
                    dialogue_durations[text] = duration
                    print(f"✓ Loaded: {text} (both characters, {duration}ms)")
            else:
                # Load single character dialogue
                if text in dialogue_files:
                    sound = self.load_dialogue_file(dialogue_files[text])
                    if sound:
                        dialogue_audio[text] = sound
                        duration = int(sound.get_length() * 1000)
                        dialogue_durations[text] = duration
                        print(f"✓ Loaded: {text} ({duration}ms)")
        
        if dialogue_audio:
            print(f"✓ Successfully loaded {len(dialogue_audio)} dialogue clips\n")
        else:
            print("⚠️  No dialogue files loaded - animation will run silently\n")

        return dialogue_audio, dialogue_durations