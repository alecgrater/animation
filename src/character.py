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
        
        # Character archetype based on color
        self.is_blue = (color == (0, 0, 255) or color[2] > color[0])  # Blue = bro type
        self.is_red = (color == (255, 0, 0) or color[0] > color[2])   # Red = pop star type

    def _draw_gradient_circle(self, screen: pygame.Surface, center: tuple, radius: int,
                             color_inner: tuple, color_outer: tuple) -> None:
        """Draw a circle with radial gradient."""
        for r in range(radius, 0, -1):
            ratio = r / radius
            # Interpolate between outer and inner colors
            r_val = int(color_outer[0] * ratio + color_inner[0] * (1 - ratio))
            g_val = int(color_outer[1] * ratio + color_inner[1] * (1 - ratio))
            b_val = int(color_outer[2] * ratio + color_inner[2] * (1 - ratio))
            pygame.draw.circle(screen, (r_val, g_val, b_val), center, r)
    
    def _draw_glow(self, screen: pygame.Surface, center: tuple, radius: int, color: tuple) -> None:
        """Draw a glowing effect around a point."""
        glow_surface = pygame.Surface((radius * 4, radius * 4), pygame.SRCALPHA)
        for i in range(3):
            alpha = 30 - i * 10
            glow_radius = radius + i * 8
            glow_color = (*color, alpha)
            pygame.draw.circle(glow_surface, glow_color, (radius * 2, radius * 2), glow_radius)
        screen.blit(glow_surface, (center[0] - radius * 2, center[1] - radius * 2))

    def draw(self, screen: pygame.Surface) -> None:
        """
        Draw the character as a whimsical, stylized stick figure.

        Args:
            screen: Pygame surface to draw on
        """
        # Calculate animation parameters
        walk_cycle = (self.walk_frame / 15) % (2 * math.pi) if self.is_walking else 0
        bob_offset = int(3 * abs(math.sin(walk_cycle))) if self.is_walking else 0
        
        if self.is_walking:
            self.walk_frame += 1

        # Idle animation - gentle breathing/floating
        idle_float = int(2 * math.sin(self.walk_frame / 30))
        
        # Base positions
        center_x = int(self.x + self.width // 2)
        base_y = int(self.y + self.height)
        
        # Head position with bobbing and floating
        head_x = center_x
        head_y = int(self.y - HEAD_RADIUS - bob_offset + idle_float)
        
        # Torso positions
        neck_y = head_y + HEAD_RADIUS
        torso_bottom_y = neck_y + 35
        
        # Hip position
        hip_y = torso_bottom_y
        
        # Create lighter and darker versions of color for gradients
        color_light = tuple(min(255, c + 80) for c in self.color)
        color_dark = tuple(max(0, c - 40) for c in self.color)
        
        # Draw head with gradient (no glow)
        self._draw_gradient_circle(screen, (head_x, head_y), HEAD_RADIUS, color_light, self.color)
        
        # Draw sparkly outline on head
        pygame.draw.circle(screen, color_light, (head_x, head_y), HEAD_RADIUS, 3)
        pygame.draw.circle(screen, BLACK, (head_x, head_y), HEAD_RADIUS, 1)
        
        # Draw sparkly eyes with shine (before character features so eyelashes can reference them)
        left_eye_x = head_x - 7
        right_eye_x = head_x + 7
        eye_y = head_y - 4
        
        # Main eye
        pygame.draw.circle(screen, BLACK, (left_eye_x, eye_y), EYE_SIZE)
        pygame.draw.circle(screen, BLACK, (right_eye_x, eye_y), EYE_SIZE)
        
        # Eye shine (white highlight)
        pygame.draw.circle(screen, (255, 255, 255), (left_eye_x - 1, eye_y - 1), 2)
        pygame.draw.circle(screen, (255, 255, 255), (right_eye_x - 1, eye_y - 1), 2)
        
        # Add character-specific features
        if self.is_blue:
            # Bro/podcast guy features
            # Baseball cap (twice as big)
            cap_y = head_y - HEAD_RADIUS - 6
            cap_height = 16
            cap_width = HEAD_RADIUS * 2 + 8
            
            # Cap crown (rounded top)
            cap_points = [
                (head_x - cap_width // 2, cap_y),
                (head_x - cap_width // 2 + 4, cap_y - cap_height),
                (head_x - cap_width // 4, cap_y - cap_height - 2),
                (head_x, cap_y - cap_height - 3),
                (head_x + cap_width // 4, cap_y - cap_height - 2),
                (head_x + cap_width // 2 - 4, cap_y - cap_height),
                (head_x + cap_width // 2, cap_y)
            ]
            pygame.draw.polygon(screen, color_dark, cap_points)
            pygame.draw.polygon(screen, BLACK, cap_points, 2)
            
            # Text on cap "sup lol" (bigger)
            font = pygame.font.Font(None, 20)
            cap_text = font.render("sup lol", True, (255, 255, 255))
            text_rect = cap_text.get_rect(center=(head_x, cap_y - cap_height // 2))
            screen.blit(cap_text, text_rect)
            
            # Cap bill (longer and more prominent)
            bill_length = 30
            bill_points = [
                (head_x - 8, cap_y),
                (head_x - bill_length - 8, cap_y + 4),
                (head_x - bill_length - 4, cap_y + 10),
                (head_x - 4, cap_y + 6)
            ]
            pygame.draw.polygon(screen, color_dark, bill_points)
            pygame.draw.polygon(screen, BLACK, bill_points, 2)
            
            # Add some detail lines on bill for realism
            pygame.draw.line(screen, BLACK,
                           (head_x - 8, cap_y + 2),
                           (head_x - bill_length - 6, cap_y + 6), 1)
            pygame.draw.line(screen, BLACK,
                           (head_x - 6, cap_y + 4),
                           (head_x - bill_length - 4, cap_y + 8), 1)
            
            # Beard/stubble (small dots)
            for bx in range(-8, 9, 3):
                for by in range(3, 10, 3):
                    if abs(bx) + by < 14:
                        pygame.draw.circle(screen, BLACK, (head_x + bx, head_y + by), 1)
            
            # Muscular build indicator (wider shoulders)
            shoulder_width_bonus = 8
        else:
            shoulder_width_bonus = 0
            
        if self.is_red:
            # Pop star/celebrity features
            # Long hair
            hair_color = (180, 140, 100) if self.color[0] > 200 else (100, 80, 60)
            # Left side hair
            for i in range(5):
                hair_x = head_x - HEAD_RADIUS + i * 2
                hair_length = 25 + i * 3
                pygame.draw.line(screen, hair_color,
                               (hair_x, head_y - HEAD_RADIUS + 5),
                               (hair_x - 8, head_y + hair_length), 3)
            # Right side hair
            for i in range(5):
                hair_x = head_x + HEAD_RADIUS - i * 2
                hair_length = 25 + i * 3
                pygame.draw.line(screen, hair_color,
                               (hair_x, head_y - HEAD_RADIUS + 5),
                               (hair_x + 8, head_y + hair_length), 3)
            
            # Sparkly headband/accessory
            headband_y = head_y - HEAD_RADIUS + 2
            pygame.draw.line(screen, (255, 215, 0),
                           (head_x - HEAD_RADIUS, headband_y),
                           (head_x + HEAD_RADIUS, headband_y), 3)
            # Sparkles on headband
            for sx in range(-HEAD_RADIUS, HEAD_RADIUS, 8):
                pygame.draw.circle(screen, (255, 255, 255), (head_x + sx, headband_y), 2)
            
            # Eyelashes
            for i in range(3):
                lash_offset = -3 + i * 3
                pygame.draw.line(screen, BLACK,
                               (left_eye_x + lash_offset, eye_y - EYE_SIZE - 1),
                               (left_eye_x + lash_offset - 1, eye_y - EYE_SIZE - 4), 1)
                pygame.draw.line(screen, BLACK,
                               (right_eye_x + lash_offset, eye_y - EYE_SIZE - 1),
                               (right_eye_x + lash_offset - 1, eye_y - EYE_SIZE - 4), 1)
            
            shoulder_width_bonus = -4  # Slimmer build
        else:
            shoulder_width_bonus = 0
        
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
        
        # Draw torso with gradient effect (multiple lines)
        for i in range(self.body_thickness):
            offset = i - self.body_thickness // 2
            ratio = abs(offset) / (self.body_thickness / 2)
            line_color = tuple(int(self.color[j] * (1 - ratio * 0.3) + color_light[j] * ratio * 0.3) for j in range(3))
            pygame.draw.line(screen, line_color, (center_x + offset, neck_y), (center_x + offset, torso_bottom_y), 1)
        
        # Add glow to torso
        glow_points = [(center_x, neck_y + 10), (center_x, torso_bottom_y - 10)]
        for point in glow_points:
            glow_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 40), (10, 10), 8)
            screen.blit(glow_surf, (point[0] - 10, point[1] - 10))
        
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
        
        # Left arm with gradient
        left_arm_end_x = center_x - 15 + int(math.sin(math.radians(left_arm_angle)) * arm_length)
        left_arm_end_y = shoulder_y + int(math.cos(math.radians(left_arm_angle)) * arm_length)
        for i in range(self.body_thickness):
            offset = i - self.body_thickness // 2
            pygame.draw.line(screen, self.color, (center_x - 5, shoulder_y), (left_arm_end_x, left_arm_end_y), 1)
        # Add sparkle at hand
        pygame.draw.circle(screen, color_light, (left_arm_end_x, left_arm_end_y), 5)
        pygame.draw.circle(screen, self.color, (left_arm_end_x, left_arm_end_y), 4)
        
        # Right arm with gradient
        right_arm_end_x = center_x + 15 + int(math.sin(math.radians(right_arm_angle)) * arm_length)
        right_arm_end_y = shoulder_y + int(math.cos(math.radians(right_arm_angle)) * arm_length)
        for i in range(self.body_thickness):
            offset = i - self.body_thickness // 2
            pygame.draw.line(screen, self.color, (center_x + 5, shoulder_y), (right_arm_end_x, right_arm_end_y), 1)
        # Add sparkle at hand
        pygame.draw.circle(screen, color_light, (right_arm_end_x, right_arm_end_y), 5)
        pygame.draw.circle(screen, self.color, (right_arm_end_x, right_arm_end_y), 4)
        
        # Animated legs
        if self.is_walking:
            # Legs alternate with walking cycle
            left_leg_angle = math.sin(walk_cycle) * 30
            right_leg_angle = -math.sin(walk_cycle) * 30
        else:
            left_leg_angle = 0
            right_leg_angle = 0
        
        leg_length = 35
        
        # Left leg (upper) with gradient
        left_knee_x = center_x - 8 + int(math.sin(math.radians(left_leg_angle)) * (leg_length * 0.6))
        left_knee_y = hip_y + int(math.cos(math.radians(left_leg_angle)) * (leg_length * 0.6))
        for i in range(self.body_thickness):
            pygame.draw.line(screen, self.color, (center_x - 5, hip_y), (left_knee_x, left_knee_y), 1)
        
        # Left leg (lower)
        if self.is_walking:
            lower_left_angle = left_leg_angle + math.sin(walk_cycle + math.pi/4) * 20
        else:
            lower_left_angle = left_leg_angle
        left_foot_x = left_knee_x + int(math.sin(math.radians(lower_left_angle)) * (leg_length * 0.5))
        left_foot_y = left_knee_y + int(math.cos(math.radians(lower_left_angle)) * (leg_length * 0.5))
        for i in range(self.body_thickness):
            pygame.draw.line(screen, self.color, (left_knee_x, left_knee_y), (left_foot_x, left_foot_y), 1)
        
        # Right leg (upper) with gradient
        right_knee_x = center_x + 8 + int(math.sin(math.radians(right_leg_angle)) * (leg_length * 0.6))
        right_knee_y = hip_y + int(math.cos(math.radians(right_leg_angle)) * (leg_length * 0.6))
        for i in range(self.body_thickness):
            pygame.draw.line(screen, self.color, (center_x + 5, hip_y), (right_knee_x, right_knee_y), 1)
        
        # Right leg (lower)
        if self.is_walking:
            lower_right_angle = right_leg_angle + math.sin(walk_cycle + math.pi/4) * 20
        else:
            lower_right_angle = right_leg_angle
        right_foot_x = right_knee_x + int(math.sin(math.radians(lower_right_angle)) * (leg_length * 0.5))
        right_foot_y = right_knee_y + int(math.cos(math.radians(lower_right_angle)) * (leg_length * 0.5))
        for i in range(self.body_thickness):
            pygame.draw.line(screen, self.color, (right_knee_x, right_knee_y), (right_foot_x, right_foot_y), 1)
        
        # Draw stylized feet with glow
        for foot_pos in [(left_foot_x, left_foot_y), (right_foot_x, right_foot_y)]:
            # Glow
            glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*self.color, 60), (8, 8), 7)
            screen.blit(glow_surf, (foot_pos[0] - 8, foot_pos[1] - 8))
            # Foot
            pygame.draw.circle(screen, color_light, foot_pos, 5)
            pygame.draw.circle(screen, self.color, foot_pos, 4)
            pygame.draw.circle(screen, color_dark, foot_pos, 2)
        

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