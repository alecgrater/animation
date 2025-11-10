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

    CAT_RUN = auto()
    WALKING_IN = auto()
    COLLISION = auto()
    KIDDING_DIALOGUE = auto()
    HEY_YA_DIALOGUE = auto()
    BUMP_SEQUENCE = auto()
    COLLISION_LOOP = auto()
    FINAL_DIALOGUE_1 = auto()
    FINAL_DIALOGUE_2 = auto()
    ALIEN_ABDUCTION = auto()
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
        collision_sound: Optional[pygame.mixer.Sound],
        meow_sound: Optional[pygame.mixer.Sound],
    ):
        """
        Initialize the animation controller.

        Args:
            char1: First character
            char2: Second character
            audio_manager: Audio manager instance
            walking_sound: Walking sound effect
            collision_sound: Collision sound effect
            meow_sound: Cat meow sound effect
        """
        self.char1 = char1
        self.char2 = char2
        self.audio_manager = audio_manager
        self.walking_sound = walking_sound
        self.collision_sound = collision_sound
        self.meow_sound = meow_sound

        self.phase = AnimationPhase.CAT_RUN
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
        
        # Subtitle animation tracking
        self.subtitle_start_time = 0
        self.subtitle_animation_offset = 0
        
        # Alien abduction tracking
        self.abduction_start_time = 0
        self.ufo_y = -100
        self.beam_alpha = 0
        
        # Cat run tracking
        self.cat_start_time = 0
        self.cat_x = -100
        self.cat_scale = 0.1
        self.meow_played = False

        # Preload all dialogue and get durations
        self.dialogue_audio, self.dialogue_durations = self._preload_dialogues()
        
        # Expose AnimationPhase for external access
        self.AnimationPhase = AnimationPhase

    def _preload_dialogues(self) -> tuple[Dict[str, pygame.mixer.Sound], Dict[str, int]]:
        """Preload all dialogue audio and get their durations."""
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
        if self.phase == AnimationPhase.CAT_RUN:
            self._update_cat_run(current_time)
        elif self.phase == AnimationPhase.WALKING_IN:
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
        elif self.phase == AnimationPhase.ALIEN_ABDUCTION:
            self._update_alien_abduction(current_time)
        elif self.phase == AnimationPhase.WALKING_OUT:
            self._update_walking_out(current_time)
        elif self.phase == AnimationPhase.FINISHED:
            self._update_finished()

    def _update_cat_run(self, current_time: int) -> None:
        """Update cat run phase - cat runs across screen super fast."""
        if self.cat_start_time == 0:
            self.cat_start_time = current_time
        
        time_elapsed = current_time - self.cat_start_time
        
        # Cat runs across in 700ms
        if time_elapsed < 700:
            # Progress from 0 to 1 over 700ms
            progress = time_elapsed / 700
            
            # Cat position (starts off-screen left, runs towards center, then past to right)
            # Runs more towards the camera (center) before going past
            self.cat_x = -100 + (SCREEN_WIDTH + 200) * progress
            
            # Cat scale - starts small, gets MUCH bigger (coming at camera), then smaller as it passes
            # Peak at 60% progress to emphasize the "coming at you" effect
            if progress < 0.6:
                # Grows from 0.1 to 1.5 (bigger than before to feel like it's coming AT the camera)
                self.cat_scale = 0.1 + (progress / 0.6) * 1.4  # 0.1 to 1.5
            else:
                # Shrinks from 1.5 to 0.1 as it runs past
                self.cat_scale = 1.5 - ((progress - 0.6) / 0.4) * 1.4  # 1.5 to 0.1
            
            # Play meow when cat is closest (around 60% progress, when it's biggest)
            if progress >= 0.55 and not self.meow_played and self.meow_sound:
                self.meow_sound.play()
                self.meow_played = True
        else:
            # Cat run finished, start main animation
            self._transition_to_walking_in()
    
    def _transition_to_walking_in(self) -> None:
        """Transition to walking in phase."""
        self.phase = AnimationPhase.WALKING_IN
    
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
        self.subtitle_start_time = current_time
        self.current_dialogue = "WATCH IT!"
        self.dialogue_speaker = "both"

        # Play collision sound effect
        if self.collision_sound:
            self.collision_sound.play()

        # Play both character dialogue files simultaneously
        if self.current_dialogue in self.dialogue_audio:
            dialogue_sounds = self.dialogue_audio[self.current_dialogue]
            if isinstance(dialogue_sounds, tuple):
                # Play both sounds simultaneously
                dialogue_sounds[0].play()
                dialogue_sounds[1].play()
            else:
                self.audio_manager.play_sound(dialogue_sounds)

    def _update_collision(self, current_time: int) -> None:
        """Update collision phase."""
        duration = self.dialogue_durations.get("WATCH IT!", COLLISION_DIALOGUE_DURATION)
        if current_time - self.dialogue_timer > duration:
            # Stop talking
            self.char1.set_talking(False)
            self.char2.set_talking(False)
            self._transition_to_kidding_dialogue(current_time)

    def _transition_to_kidding_dialogue(self, current_time: int) -> None:
        """Transition to kidding dialogue phase."""
        self.phase = AnimationPhase.KIDDING_DIALOGUE
        self.dialogue_timer = current_time
        self.subtitle_start_time = current_time
        self.current_dialogue = "Just kidding, running into people is fun!"
        self.dialogue_speaker = "char1"
        # Char1 talking
        self.char1.set_talking(True)
        self.char2.set_talking(False)

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_kidding_dialogue(self, current_time: int) -> None:
        """Update kidding dialogue phase."""
        duration = self.dialogue_durations.get("Just kidding, running into people is fun!", KIDDING_DIALOGUE_DURATION)
        if current_time - self.dialogue_timer > duration:
            # Stop talking
            self.char1.set_talking(False)
            self._transition_to_hey_ya_dialogue(current_time)

    def _transition_to_hey_ya_dialogue(self, current_time: int) -> None:
        """Transition to hey ya dialogue phase."""
        self.phase = AnimationPhase.HEY_YA_DIALOGUE
        self.dialogue_timer = current_time
        self.subtitle_start_time = current_time
        self.current_dialogue = "Hey ya!"
        self.dialogue_speaker = "char2"
        # Char2 talking
        self.char1.set_talking(False)
        self.char2.set_talking(True)

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_hey_ya_dialogue(self, current_time: int) -> None:
        """Update hey ya dialogue phase."""
        duration = self.dialogue_durations.get("Hey ya!", HEY_YA_DIALOGUE_DURATION)
        if current_time - self.dialogue_timer > duration:
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
                # Play collision sound
                if self.collision_sound:
                    self.collision_sound.play()
                
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
            # Play collision sound
            if self.collision_sound:
                self.collision_sound.play()

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
        self.subtitle_start_time = current_time
        self.current_dialogue = "Okay I have to go to work"
        self.dialogue_speaker = "char1"

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_final_dialogue_1(self, current_time: int) -> None:
        """Update final dialogue 1 phase."""
        duration = self.dialogue_durations.get("Okay I have to go to work", FINAL_DIALOGUE_1_DURATION)
        if current_time - self.dialogue_timer > duration:
            # Stop talking
            self.char1.set_talking(False)
            self._transition_to_final_dialogue_2(current_time)

    def _transition_to_final_dialogue_2(self, current_time: int) -> None:
        """Transition to final dialogue 2 phase."""
        self.phase = AnimationPhase.FINAL_DIALOGUE_2
        self.dialogue_timer = current_time
        self.subtitle_start_time = current_time
        self.current_dialogue = "I don't care"
        self.dialogue_speaker = "char2"
        # Char2 talking
        self.char1.set_talking(False)
        self.char2.set_talking(True)

        if self.current_dialogue in self.dialogue_audio:
            self.audio_manager.play_sound(self.dialogue_audio[self.current_dialogue])

    def _update_final_dialogue_2(self, current_time: int) -> None:
        """Update final dialogue 2 phase."""
        duration = self.dialogue_durations.get("I don't care", FINAL_DIALOGUE_2_DURATION)
        # Wait 400ms after dialogue ends before abduction
        if current_time - self.dialogue_timer > duration + 400:
            # Stop talking
            self.char2.set_talking(False)
            self._transition_to_alien_abduction(current_time)
    
    def _transition_to_alien_abduction(self, current_time: int) -> None:
        """Transition to alien abduction phase."""
        self.phase = AnimationPhase.ALIEN_ABDUCTION
        self.abduction_start_time = current_time
        self.char1.set_speed(0)
        self.char2.set_speed(0)
        self.char1.set_walking(False)
        self.char2.set_walking(False)
        self.current_dialogue = ""
        self.ufo_y = -100
        self.beam_alpha = 0
    
    def _update_alien_abduction(self, current_time: int) -> None:
        """Update alien abduction phase - char2 gets beamed up casually."""
        time_elapsed = current_time - self.abduction_start_time
        
        # UFO descends (0-1000ms)
        if time_elapsed < 1000:
            self.ufo_y = -100 + (time_elapsed / 1000) * 150  # Descend to y=50
        else:
            self.ufo_y = 50
        
        # Beam appears (500-1500ms)
        if 500 < time_elapsed < 1500:
            self.beam_alpha = min(150, (time_elapsed - 500) / 1000 * 150)
        elif time_elapsed >= 1500:
            self.beam_alpha = 150
        
        # Char2 floats up (1500-3500ms)
        if time_elapsed > 1500:
            lift_progress = min(1.0, (time_elapsed - 1500) / 2000)
            self.char2.y = self.char2.y - lift_progress * 2  # Slow upward movement
        
        # After 4 seconds, transition to char1 walking out alone
        if time_elapsed > 4000:
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

    def _create_gradient_surface(self, text: str, font: pygame.font.Font,
                                 color_top: tuple, color_bottom: tuple) -> pygame.Surface:
        """
        Create a text surface with vertical gradient fill.
        
        Args:
            text: The text to render
            font: The font to use
            color_top: RGB color for top of gradient
            color_bottom: RGB color for bottom of gradient
            
        Returns:
            Surface with gradient text
        """
        # Create base text surface
        text_surface = font.render(text, True, (255, 255, 255))
        width, height = text_surface.get_size()
        
        # Create gradient surface
        gradient_surface = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Draw gradient
        for y in range(height):
            # Interpolate between top and bottom colors
            ratio = y / height
            r = int(color_top[0] * (1 - ratio) + color_bottom[0] * ratio)
            g = int(color_top[1] * (1 - ratio) + color_bottom[1] * ratio)
            b = int(color_top[2] * (1 - ratio) + color_bottom[2] * ratio)
            pygame.draw.line(gradient_surface, (r, g, b), (0, y), (width, y))
        
        # Apply text as alpha mask
        gradient_surface.blit(text_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
        
        return gradient_surface

    def draw_dialogue(self, screen: pygame.Surface) -> None:
        """
        Draw the current dialogue on screen with enhanced styling and animations.

        Args:
            screen: Pygame surface to draw on
        """
        if not self.current_dialogue:
            return

        current_time = pygame.time.get_ticks()
        time_since_start = current_time - self.subtitle_start_time
        
        # Larger font sizes
        font_size = 64 if self.dialogue_speaker == "both" else 48
        if self.dialogue_speaker == "system":
            font_size = 56

        font = pygame.font.Font(None, font_size)
        
        # Determine colors and position based on speaker
        if self.dialogue_speaker == "both":
            gradient_top = (255, 100, 100)  # Light red
            gradient_bottom = (200, 0, 0)   # Dark red
            outline_color = (100, 0, 0)     # Very dark red
            base_center = (SCREEN_WIDTH // 2, 100)
        elif self.dialogue_speaker == "char1":
            gradient_top = (100, 150, 255)  # Light blue
            gradient_bottom = (0, 50, 200)  # Dark blue
            outline_color = (0, 0, 100)     # Very dark blue
            base_center = (self.char1.get_center_x(), self.char1.y - 80)
        elif self.dialogue_speaker == "char2":
            gradient_top = (255, 100, 100)  # Light red
            gradient_bottom = (200, 0, 0)   # Dark red
            outline_color = (100, 0, 0)     # Very dark red
            base_center = (self.char2.get_center_x(), self.char2.y - 80)
        else:  # system
            gradient_top = (255, 255, 255)  # White
            gradient_bottom = (200, 200, 200)  # Light gray
            outline_color = (50, 50, 50)    # Dark gray
            base_center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)

        # Animation effects
        import math
        
        # 1. Bounce-in effect (first 300ms)
        bounce_duration = 300
        if time_since_start < bounce_duration:
            progress = time_since_start / bounce_duration
            # Elastic ease-out
            scale = 1.0 + 0.3 * math.sin(progress * math.pi * 2) * (1 - progress)
            alpha = int(255 * progress)
        else:
            scale = 1.0
            alpha = 255
            
        # 2. Gentle floating motion (continuous)
        float_offset_y = math.sin(time_since_start / 500) * 5
        
        # 3. Subtle rotation wobble (continuous, very slight)
        rotation_angle = math.sin(time_since_start / 800) * 2  # ±2 degrees
        
        # 4. Slight horizontal sway (continuous)
        sway_offset_x = math.sin(time_since_start / 600) * 8
        
        # Apply animation offsets to center position
        animated_center = (
            int(base_center[0] + sway_offset_x),
            int(base_center[1] + float_offset_y)
        )
        
        # Create outline by rendering text multiple times with offset
        outline_thickness = 3
        outline_offsets = []
        for x in range(-outline_thickness, outline_thickness + 1):
            for y in range(-outline_thickness, outline_thickness + 1):
                if x != 0 or y != 0:
                    outline_offsets.append((x, y))
        
        # Render base text for sizing
        temp_surface = font.render(self.current_dialogue, True, (255, 255, 255))
        original_rect = temp_surface.get_rect(center=animated_center)
        
        # Create a larger surface to accommodate rotation and scaling
        max_dimension = int(max(original_rect.width, original_rect.height) * 1.5)
        render_surface = pygame.Surface((max_dimension, max_dimension), pygame.SRCALPHA)
        render_center = (max_dimension // 2, max_dimension // 2)
        
        # Draw outline on render surface
        for offset_x, offset_y in outline_offsets:
            outline_surface = font.render(self.current_dialogue, True, outline_color)
            outline_rect = outline_surface.get_rect(center=(render_center[0] + offset_x,
                                                            render_center[1] + offset_y))
            render_surface.blit(outline_surface, outline_rect)
        
        # Draw gradient fill text on render surface
        gradient_text = self._create_gradient_surface(self.current_dialogue, font,
                                                      gradient_top, gradient_bottom)
        gradient_rect = gradient_text.get_rect(center=render_center)
        render_surface.blit(gradient_text, gradient_rect)
        
        # Apply scale
        if scale != 1.0:
            new_width = int(render_surface.get_width() * scale)
            new_height = int(render_surface.get_height() * scale)
            render_surface = pygame.transform.scale(render_surface, (new_width, new_height))
        
        # Apply rotation
        if rotation_angle != 0:
            render_surface = pygame.transform.rotate(render_surface, rotation_angle)
        
        # Apply alpha
        if alpha < 255:
            render_surface.set_alpha(alpha)
        
        # Blit to screen centered at animated position
        final_rect = render_surface.get_rect(center=animated_center)
        screen.blit(render_surface, final_rect)