"""Character class for the animation."""

import math
import pygame

from .config import (
    BLACK,
    CHARACTER_WIDTH,
    CHARACTER_HEIGHT,
    CHARACTER_SPEED,
    HEAD_RADIUS,
    EYE_SIZE,
)


class Character:
    """Represents an animated stick figure character with advanced animations."""

    def __init__(
        self, x: float, y: float, color: tuple[int, int, int], name: str, voice: str = "alloy"
    ):
        """
        Initialize a character.

        Args:
            x: Initial x position
            y: Initial y position
            color: RGB color tuple
            name: Character name
            voice: TTS voice to use for this character
        """
        self.x = x
        self.y = y
        self.color = color
        self.name = name
        self.voice = voice
        self.width = CHARACTER_WIDTH
        self.height = CHARACTER_HEIGHT
        self.speed = CHARACTER_SPEED
        self.direction = 1  # 1 for right, -1 for left
        self.is_smiling = False
        self.is_walking = False
        self.is_talking = False
        self.walk_frame = 0
        self.talk_frame = 0
        self.body_thickness = 4  # Thickness of body lines

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the character as an advanced stick figure.

        Args:
            screen: Pygame surface to draw on
        """
        # Calculate animation parameters
        walk_cycle = (self.walk_frame / 15) % (2 * math.pi) if self.is_walking else 0
        bob_offset = int(3 * abs(math.sin(walk_cycle))) if self.is_walking else 0
        
        if self.is_walking:
            self.walk_frame += 1

        # Base positions
        center_x = int(self.x + self.width // 2)
        base_y = int(self.y + self.height)
        
        # Head position with bobbing
        head_x = center_x
        head_y = int(self.y - HEAD_RADIUS - bob_offset)
        
        # Torso positions
        neck_y = head_y + HEAD_RADIUS
        torso_bottom_y = neck_y + 35
        
        # Hip position
        hip_y = torso_bottom_y
        
        # Draw head (circle with outline)
        pygame.draw.circle(screen, self.color, (head_x, head_y), HEAD_RADIUS)
        pygame.draw.circle(screen, BLACK, (head_x, head_y), HEAD_RADIUS, 2)
        
        # Draw eyes
        left_eye_x = head_x - 7
        right_eye_x = head_x + 7
        eye_y = head_y - 4
        pygame.draw.circle(screen, BLACK, (left_eye_x, eye_y), EYE_SIZE)
        pygame.draw.circle(screen, BLACK, (right_eye_x, eye_y), EYE_SIZE)
        
        # Draw mouth - ALWAYS smiling (never frowning!)
        if self.is_talking:
            # Animate mouth opening and closing while talking
            self.talk_frame += 1
            mouth_open = (self.talk_frame // 5) % 2 == 0  # Toggle every 5 frames
            
            if mouth_open:
                # Open mouth (circle/oval) - still shows happiness
                mouth_rect = pygame.Rect(head_x - 6, head_y + 6, 12, 10)
                pygame.draw.ellipse(screen, BLACK, mouth_rect, 2)
            else:
                # Closed mouth - SMILE (upward arc)
                mouth_rect = pygame.Rect(head_x - 8, head_y + 5, 16, 8)
                pygame.draw.arc(screen, BLACK, mouth_rect, 0, math.pi, 2)
        elif self.is_smiling:
            # Draw big smile (upward arc)
            mouth_rect = pygame.Rect(head_x - 10, head_y + 3, 20, 10)
            pygame.draw.arc(screen, BLACK, mouth_rect, 0, math.pi, 3)
        else:
            # Draw small smile (upward arc) - DEFAULT IS ALWAYS SMILING
            mouth_rect = pygame.Rect(head_x - 8, head_y + 5, 16, 8)
            pygame.draw.arc(screen, BLACK, mouth_rect, 0, math.pi, 2)
        
        # Draw torso (thicker line)
        pygame.draw.line(screen, self.color, (center_x, neck_y), (center_x, torso_bottom_y), self.body_thickness)
        
        # Animated arms
        if self.is_walking:
            # Arms swing opposite to legs
            arm_swing = math.sin(walk_cycle) * 25
            left_arm_angle = -arm_swing
            right_arm_angle = arm_swing
        else:
            left_arm_angle = -15
            right_arm_angle = 15
        
        shoulder_y = neck_y + 8
        arm_length = 25
        
        # Left arm
        left_arm_end_x = center_x - 15 + int(math.sin(math.radians(left_arm_angle)) * arm_length)
        left_arm_end_y = shoulder_y + int(math.cos(math.radians(left_arm_angle)) * arm_length)
        pygame.draw.line(screen, self.color, (center_x - 5, shoulder_y), (left_arm_end_x, left_arm_end_y), self.body_thickness)
        
        # Right arm
        right_arm_end_x = center_x + 15 + int(math.sin(math.radians(right_arm_angle)) * arm_length)
        right_arm_end_y = shoulder_y + int(math.cos(math.radians(right_arm_angle)) * arm_length)
        pygame.draw.line(screen, self.color, (center_x + 5, shoulder_y), (right_arm_end_x, right_arm_end_y), self.body_thickness)
        
        # Animated legs
        if self.is_walking:
            # Legs alternate with walking cycle
            left_leg_angle = math.sin(walk_cycle) * 30
            right_leg_angle = -math.sin(walk_cycle) * 30
        else:
            left_leg_angle = 0
            right_leg_angle = 0
        
        leg_length = 35
        
        # Left leg (upper)
        left_knee_x = center_x - 8 + int(math.sin(math.radians(left_leg_angle)) * (leg_length * 0.6))
        left_knee_y = hip_y + int(math.cos(math.radians(left_leg_angle)) * (leg_length * 0.6))
        pygame.draw.line(screen, self.color, (center_x - 5, hip_y), (left_knee_x, left_knee_y), self.body_thickness)
        
        # Left leg (lower)
        if self.is_walking:
            lower_left_angle = left_leg_angle + math.sin(walk_cycle + math.pi/4) * 20
        else:
            lower_left_angle = left_leg_angle
        left_foot_x = left_knee_x + int(math.sin(math.radians(lower_left_angle)) * (leg_length * 0.5))
        left_foot_y = left_knee_y + int(math.cos(math.radians(lower_left_angle)) * (leg_length * 0.5))
        pygame.draw.line(screen, self.color, (left_knee_x, left_knee_y), (left_foot_x, left_foot_y), self.body_thickness)
        
        # Right leg (upper)
        right_knee_x = center_x + 8 + int(math.sin(math.radians(right_leg_angle)) * (leg_length * 0.6))
        right_knee_y = hip_y + int(math.cos(math.radians(right_leg_angle)) * (leg_length * 0.6))
        pygame.draw.line(screen, self.color, (center_x + 5, hip_y), (right_knee_x, right_knee_y), self.body_thickness)
        
        # Right leg (lower)
        if self.is_walking:
            lower_right_angle = right_leg_angle + math.sin(walk_cycle + math.pi/4) * 20
        else:
            lower_right_angle = right_leg_angle
        right_foot_x = right_knee_x + int(math.sin(math.radians(lower_right_angle)) * (leg_length * 0.5))
        right_foot_y = right_knee_y + int(math.cos(math.radians(lower_right_angle)) * (leg_length * 0.5))
        pygame.draw.line(screen, self.color, (right_knee_x, right_knee_y), (right_foot_x, right_foot_y), self.body_thickness)
        
        # Draw feet (small circles)
        pygame.draw.circle(screen, self.color, (left_foot_x, left_foot_y), 4)
        pygame.draw.circle(screen, self.color, (right_foot_x, right_foot_y), 4)

    def move(self) -> None:
        """Move the character based on speed and direction."""
        self.x += self.speed * self.direction

    def get_center_x(self) -> float:
        """Get the x coordinate of the character's center."""
        return self.x + self.width // 2

    def get_rect(self) -> pygame.Rect:
        """Get the character's bounding rectangle."""
        return pygame.Rect(self.x, self.y, self.width, self.height)

    def set_walking(self, walking: bool) -> None:
        """Set the walking state of the character."""
        self.is_walking = walking

    def set_smiling(self, smiling: bool) -> None:
        """Set the smiling state of the character."""
        self.is_smiling = smiling

    def set_talking(self, talking: bool) -> None:
        """Set the talking state of the character."""
        self.is_talking = talking
        if not talking:
            self.talk_frame = 0  # Reset talk animation when done

    def set_speed(self, speed: float) -> None:
        """Set the character's movement speed."""
        self.speed = speed

    def reverse_direction(self) -> None:
        """Reverse the character's movement direction."""
        self.direction *= -1