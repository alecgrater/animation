"""Animation state machine and logic."""

from enum import Enum, auto
from typing import Optional, Dict

import pygame

from .audio import AudioManager
from .character import Character
from .config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLLISION_DIALOGUE_DURATION,
    KIDDING_DIALOGUE_DURATION,
    HEY_YA_DIALOGUE_DURATION,
    COLLISION_LOOP_DURATION,
    FINAL_DIALOGUE_1_DURATION,
    FINAL_DIALOGUE_2_DURATION,
    WALKING_SOUND_INTERVAL,
    COLLISION_LOOP_SOUND_INTERVAL,
    BLACK,
    RED,
    BLUE,
)


class AnimationPhase(Enum):
    """Enumeration of animation phases."""

    WALKING_IN = auto()
    COLLISION = auto()
    KIDDING_DIALOGUE = auto()
    HEY_YA_DIALOGUE = auto()
    BUMP_SEQUENCE = auto()
    COLLISION_LOOP = auto()
    FINAL_DIALOGUE_1 = auto()
    FINAL_DIALOGUE_2 = auto()
    WALKING_OUT = auto()
    FINISHED = auto()


class AnimationController:
    """Controls the animation state machine and character interactions."""

    def __init__(
        self,
        char1: Character,
        char2: Character,
        audio_manager: AudioManager,
        walking_sound: Optional[pygame.mixer.Sound],
    ):
        """
        Initialize the animation controller.

        Args:
            char1: First character
            char2: Second character
            audio_manager: Audio manager instance
            walking_sound: Walking sound effect
        """
        self.char1 = char1
        self.char2 = char2
        self.audio_manager = audio_manager
        self.walking_sound = walking_sound

        self.phase = AnimationPhase.WALKING_IN
        self.dialogue_timer = 0
        self.collision_start_time = 0
        self.walking_sound_timer = 0
        self.current_dialogue = ""
        self.dialogue_speaker = ""
        self.finished_time = None
        
        # Bump sequence tracking
        self.bump_count = 0
        self.bump_state = "approaching"  # approaching, backing_up
        self.bump_timer = 0

        # Preload all dialogue
        self.dialogue_audio = self._preload_dialogues()
        
        # Expose AnimationPhase for external access
        self.AnimationPhase = AnimationPhase

    def _preload_dialogues(self) -> Dict[str, pygame.mixer.Sound]:
        """Preload all dialogue audio."""
        dialogues = [
            ("WATCH IT!", "both", "nova"),
            ("Just kidding, running into people is fun!", "char1", self.char1.voice),
            ("Hey ya!", "char2", self.char2.voice),
            ("Okay I have to go to work", "char1", self.char1.voice),
            ("I don't care", "char2", self.char2.voice),
        ]
        return self.audio_manager.preload_dialogue(dialogues)

    def update(self, current_time: int) -> None:
        """
        Update the animation state.

        Args:
            current_time: Current time in milliseconds from pygame.time.get_ticks()
        """
        if self.phase == AnimationPhase.WALKING_IN:
            self._update_walking_in(current_time)
        elif self.phase == AnimationPhase.COLLISION:
            self._update_collision(current_time)
        elif self.phase == AnimationPhase.KIDDING_DIALOGUE:
            self._update_kidding_dialogue(current_time)
        elif self.phase == AnimationPhase.HEY_YA_DIALOGUE:
            self._update_hey_ya_dialogue(current_time)
        elif self.phase == AnimationPhase.BUMP_SEQUENCE:
            self._update_bump_sequence(current_time)
        elif self.phase == AnimationPhase.COLLISION_LOOP:
            self._update_collision_loop(current_time)
        elif self.phase == AnimationPhase.FINAL_DIALOGUE_1:
            self._update_final_dialogue_1(current_time)
        elif self.phase == AnimationPhase.FINAL_DIALOGUE_2:
            self._update_final_dialogue_2(current_time)
        elif self.phase == AnimationPhase.WALKING_OUT:
            self._update_walking_out(current_time)
        elif self.phase == AnimationPhase.FINISHED:
            self._update_finished()

    def _update_walking_in(self, current_time: int) -> None:
        """Update walking in phase."""
        self.char1.set_walking(True)
        self.char2.set_walking(True)
        self.char1.move()
        self.char2.move()

        # Start walking sound loop if not already playing
        self._manage_walking_sound()

        # Check if they're close to center and about to collide
        if (
            self.char1.get_center_x() >= SCREEN_WIDTH // 2 - 50
            and self.char2.get_center_x() <= SCREEN_WIDTH // 2 + 50
        ):
            self._transition_to_collision(current_time)

    def _transition_to_collision(self, current_time: int) -> None:
        """Transition to collision phase."""
        self.phase = AnimationPhase.COLLISION
        self.char1.set_speed(0)
        self.char2.set_speed(0)
        self.char1.set_walking(False)
        self.char2.set_walking(False)
        # Make them smile immediately after collision
        self.char1.set_smiling(True)
        self.char2.set_smiling(True)
        # Both characters talking
        self.char1.set_talking(True)
        self.char2.set_talking(True)
        # Stop walking sound immediately
        self.audio_manager.stop_current_sound()
        self.dialogue_timer = current_time
        self.current_dialogue = "WATCH IT!"
        self.dialogue_speaker = "both"

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_collision(self, current_time: int) -> None:
        """Update collision phase."""
        if current_time - self.dialogue_timer > COLLISION_DIALOGUE_DURATION:
            # Stop talking
            self.char1.set_talking(False)
            self.char2.set_talking(False)
            self._transition_to_kidding_dialogue(current_time)

    def _transition_to_kidding_dialogue(self, current_time: int) -> None:
        """Transition to kidding dialogue phase."""
        self.phase = AnimationPhase.KIDDING_DIALOGUE
        self.dialogue_timer = current_time
        self.current_dialogue = "Just kidding, running into people is fun!"
        self.dialogue_speaker = "char1"
        # Char1 talking
        self.char1.set_talking(True)
        self.char2.set_talking(False)

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_kidding_dialogue(self, current_time: int) -> None:
        """Update kidding dialogue phase."""
        if current_time - self.dialogue_timer > KIDDING_DIALOGUE_DURATION:
            # Stop talking
            self.char1.set_talking(False)
            self._transition_to_hey_ya_dialogue(current_time)

    def _transition_to_hey_ya_dialogue(self, current_time: int) -> None:
        """Transition to hey ya dialogue phase."""
        self.phase = AnimationPhase.HEY_YA_DIALOGUE
        self.dialogue_timer = current_time
        self.current_dialogue = "Hey ya!"
        self.dialogue_speaker = "char2"
        # Char2 talking
        self.char1.set_talking(False)
        self.char2.set_talking(True)

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_hey_ya_dialogue(self, current_time: int) -> None:
        """Update hey ya dialogue phase."""
        if current_time - self.dialogue_timer > HEY_YA_DIALOGUE_DURATION:
            # Stop talking
            self.char2.set_talking(False)
            self._transition_to_bump_sequence(current_time)

    def _transition_to_bump_sequence(self, current_time: int) -> None:
        """Transition to bump sequence phase."""
        self.phase = AnimationPhase.BUMP_SEQUENCE
        self.bump_count = 0
        self.bump_state = "approaching"
        self.bump_timer = current_time
        self.char1.set_smiling(True)
        self.char2.set_smiling(True)
        self.char1.set_speed(3)
        self.char2.set_speed(3)
        self.char1.set_walking(True)
        self.char2.set_walking(True)
        self.char1.direction = 1  # Moving toward each other
        self.char2.direction = -1
        self.current_dialogue = ""

    def _update_bump_sequence(self, current_time: int) -> None:
        """Update bump sequence - characters bump 5 times with backing up between."""
        if self.bump_state == "approaching":
            # Move toward each other
            self.char1.move()
            self.char2.move()
            self._manage_walking_sound()
            
            # Check for collision
            if self.char1.get_rect().colliderect(self.char2.get_rect()):
                self.bump_count += 1
                self.bump_state = "backing_up"
                self.bump_timer = current_time
                # Reverse directions to back up
                self.char1.direction = -1
                self.char2.direction = 1
                
        elif self.bump_state == "backing_up":
            # Back up for a short time
            self.char1.move()
            self.char2.move()
            self._manage_walking_sound()
            
            # After backing up for 0.5 seconds, approach again
            if current_time - self.bump_timer > 500:
                if self.bump_count >= 5:
                    # Done with bump sequence, move to collision loop
                    self._transition_to_collision_loop(current_time)
                else:
                    # Approach again
                    self.bump_state = "approaching"
                    self.char1.direction = 1
                    self.char2.direction = -1

    def _transition_to_collision_loop(self, current_time: int) -> None:
        """Transition to collision loop phase."""
        self.phase = AnimationPhase.COLLISION_LOOP
        self.collision_start_time = current_time
        self.char1.set_smiling(True)
        self.char2.set_smiling(True)
        self.char1.set_speed(2)
        self.char2.set_speed(2)
        self.char1.set_walking(True)
        self.char2.set_walking(True)
        self.current_dialogue = ""

    def _update_collision_loop(self, current_time: int) -> None:
        """Update collision loop phase."""
        collision_loop_time = current_time - self.collision_start_time

        # Move characters back and forth
        self.char1.move()
        self.char2.move()

        # Manage walking sound loop
        self._manage_walking_sound()

        # Bounce off each other
        if self.char1.get_rect().colliderect(self.char2.get_rect()):
            self.char1.reverse_direction()
            self.char2.reverse_direction()
            # Small separation to prevent sticking
            self.char1.x -= 5
            self.char2.x += 5

        # Bounce off screen edges
        if self.char1.x < 0:
            self.char1.direction = 1
        elif self.char1.x > SCREEN_WIDTH - self.char1.width:
            self.char1.direction = -1

        if self.char2.x < 0:
            self.char2.direction = 1
        elif self.char2.x > SCREEN_WIDTH - self.char2.width:
            self.char2.direction = -1

        # After 6 seconds, move to final dialogue
        if collision_loop_time > COLLISION_LOOP_DURATION:
            self._transition_to_final_dialogue_1(current_time)

    def _transition_to_final_dialogue_1(self, current_time: int) -> None:
        """Transition to final dialogue 1 phase."""
        self.phase = AnimationPhase.FINAL_DIALOGUE_1
        self.char1.set_speed(0)
        self.char2.set_speed(0)
        # Keep them smiling!
        self.char1.set_smiling(True)
        self.char2.set_smiling(True)
        self.char1.set_walking(False)
        self.char2.set_walking(False)
        # Char1 talking
        self.char1.set_talking(True)
        self.char2.set_talking(False)
        # Stop walking sound immediately
        self.audio_manager.stop_current_sound()
        self.dialogue_timer = current_time
        self.current_dialogue = "Okay I have to go to work"
        self.dialogue_speaker = "char1"

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_final_dialogue_1(self, current_time: int) -> None:
        """Update final dialogue 1 phase."""
        if current_time - self.dialogue_timer > FINAL_DIALOGUE_1_DURATION:
            # Stop talking
            self.char1.set_talking(False)
            self._transition_to_final_dialogue_2(current_time)

    def _transition_to_final_dialogue_2(self, current_time: int) -> None:
        """Transition to final dialogue 2 phase."""
        self.phase = AnimationPhase.FINAL_DIALOGUE_2
        self.dialogue_timer = current_time
        self.current_dialogue = "I don't care"
        self.dialogue_speaker = "char2"
        # Char2 talking
        self.char1.set_talking(False)
        self.char2.set_talking(True)

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_final_dialogue_2(self, current_time: int) -> None:
        """Update final dialogue 2 phase."""
        if current_time - self.dialogue_timer > FINAL_DIALOGUE_2_DURATION:
            # Stop talking
            self.char2.set_talking(False)
            self._transition_to_walking_out()

    def _transition_to_walking_out(self) -> None:
        """Transition to walking out phase."""
        self.phase = AnimationPhase.WALKING_OUT
        self.char1.set_speed(3)
        self.char2.set_speed(3)
        self.char1.direction = 1  # char1 exits right
        self.char2.direction = -1  # char2 exits left
        self.char1.set_walking(True)
        self.char2.set_walking(True)
        # Keep them smiling as they leave!
        self.char1.set_smiling(True)
        self.char2.set_smiling(True)
        self.current_dialogue = ""

    def _update_walking_out(self, current_time: int) -> None:
        """Update walking out phase."""
        self.char1.move()
        self.char2.move()

        # Manage walking sound loop
        self._manage_walking_sound()

        # Check if both characters are off screen
        if self.char1.x > SCREEN_WIDTH and self.char2.x < -self.char2.width:
            self._transition_to_finished()

    def _transition_to_finished(self) -> None:
        """Transition to finished phase."""
        self.phase = AnimationPhase.FINISHED
        self.char1.set_walking(False)
        self.char2.set_walking(False)
        # Keep them smiling even at the end!
        self.char1.set_smiling(True)
        self.char2.set_smiling(True)
        # Stop walking sound immediately
        self.audio_manager.stop_current_sound()
        self.finished_time = None

    def _update_finished(self) -> None:
        """Update finished phase - marks time for auto-close."""
        if self.finished_time is None:
            self.finished_time = pygame.time.get_ticks()
        # No dialogue shown, animation will auto-close
        self.current_dialogue = ""
        self.dialogue_speaker = ""

    def _manage_walking_sound(self) -> None:
        """
        Manage walking sound - start looping when walking, stop when not walking.
        This ensures the sound is directly tied to character movement.
        """
        # Check if any character is actually walking with speed > 0
        is_anyone_walking = (
            (self.char1.is_walking and self.char1.speed > 0) or
            (self.char2.is_walking and self.char2.speed > 0)
        )
        
        if is_anyone_walking:
            # Start walking sound loop if not already playing
            if self.walking_sound and not self.audio_manager.is_sound_playing(self.walking_sound):
                self.audio_manager.play_looping_sound(self.walking_sound)
        else:
            # Stop walking sound immediately if no one is walking
            if self.walking_sound and self.audio_manager.is_sound_playing(self.walking_sound):
                self.audio_manager.stop_current_sound()

    def draw_dialogue(self, screen: pygame.Surface) -> None:
        """
        Draw the current dialogue on screen.

        Args:
            screen: Pygame surface to draw on
        """
        if not self.current_dialogue:
            return

        font_size = 36 if self.dialogue_speaker == "both" else 24
        if self.dialogue_speaker == "system":
            font_size = 32

        font = pygame.font.Font(None, font_size)
        text_surface = font.render(self.current_dialogue, True, BLACK)
        text_rect = text_surface.get_rect()

        if self.dialogue_speaker == "both":
            text_surface = font.render(self.current_dialogue, True, RED)
            text_rect.center = (SCREEN_WIDTH // 2, 100)
        elif self.dialogue_speaker == "char1":
            text_surface = font.render(self.current_dialogue, True, BLUE)
            text_rect.center = (self.char1.get_center_x(), self.char1.y - 80)
        elif self.dialogue_speaker == "char2":
            text_surface = font.render(self.current_dialogue, True, RED)
            text_rect.center = (self.char2.get_center_x(), self.char2.y - 80)
        elif self.dialogue_speaker == "system":
            text_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        screen.blit(text_surface, text_rect)