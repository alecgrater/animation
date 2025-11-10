"""Main entry point for the character animation."""

import sys
import math

import pygame

from src.animation import AnimationController
from src.audio import AudioManager
from src.character import Character
from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    WHITE,
    BLUE,
    RED,
    AUDIO_SAMPLE_RATE,
    AUDIO_BUFFER_SIZE,
)


def draw_park_background(screen: pygame.Surface) -> None:
    """Draw a park setting background."""
    # Sky gradient (light blue to lighter blue)
    for y in range(SCREEN_HEIGHT // 2):
        ratio = y / (SCREEN_HEIGHT // 2)
        r = int(135 + (180 - 135) * ratio)
        g = int(206 + (220 - 206) * ratio)
        b = int(235 + (245 - 235) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # Grass (green gradient)
    grass_start_y = SCREEN_HEIGHT // 2
    for y in range(grass_start_y, SCREEN_HEIGHT):
        ratio = (y - grass_start_y) / (SCREEN_HEIGHT - grass_start_y)
        r = int(100 + (80 - 100) * ratio)
        g = int(180 + (150 - 180) * ratio)
        b = int(100 + (80 - 100) * ratio)
        pygame.draw.line(screen, (r, g, b), (0, y), (SCREEN_WIDTH, y))
    
    # Path/walkway (light gray)
    path_y = SCREEN_HEIGHT - 200
    path_height = 120
    pygame.draw.rect(screen, (200, 200, 200),
                    (0, path_y, SCREEN_WIDTH, path_height))
    
    # Path edge lines
    pygame.draw.line(screen, (150, 150, 150),
                    (0, path_y), (SCREEN_WIDTH, path_y), 3)
    pygame.draw.line(screen, (150, 150, 150),
                    (0, path_y + path_height), (SCREEN_WIDTH, path_y + path_height), 3)
    
    # Trees in background (simple)
    tree_positions = [100, 300, 500, 700]
    for tree_x in tree_positions:
        # Tree trunk
        trunk_width = 20
        trunk_height = 60
        trunk_y = grass_start_y + 40
        pygame.draw.rect(screen, (101, 67, 33),
                        (tree_x - trunk_width // 2, trunk_y, trunk_width, trunk_height))
        
        # Tree foliage (circles)
        foliage_y = trunk_y - 20
        pygame.draw.circle(screen, (34, 139, 34), (tree_x, foliage_y), 40)
        pygame.draw.circle(screen, (50, 150, 50), (tree_x - 20, foliage_y + 10), 30)
        pygame.draw.circle(screen, (50, 150, 50), (tree_x + 20, foliage_y + 10), 30)
    
    # Clouds (simple white circles)
    cloud_positions = [(150, 80), (400, 60), (650, 90)]
    for cloud_x, cloud_y in cloud_positions:
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x, cloud_y), 30)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x + 25, cloud_y), 25)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x - 25, cloud_y), 25)
        pygame.draw.circle(screen, (255, 255, 255), (cloud_x + 10, cloud_y - 15), 20)
    
    # Sun
    sun_x, sun_y = 700, 100
    # Sun glow
    for i in range(5, 0, -1):
        alpha_surf = pygame.Surface((100, 100), pygame.SRCALPHA)
        pygame.draw.circle(alpha_surf, (255, 255, 0, 30), (50, 50), 30 + i * 5)
        screen.blit(alpha_surf, (sun_x - 50, sun_y - 50))
    # Sun core
    pygame.draw.circle(screen, (255, 255, 0), (sun_x, sun_y), 30)
    pygame.draw.circle(screen, (255, 255, 150), (sun_x, sun_y), 25)
    
    # Flowers/bushes on grass
    flower_positions = [(80, grass_start_y + 20), (250, grass_start_y + 30),
                       (450, grass_start_y + 25), (620, grass_start_y + 35)]
    for fx, fy in flower_positions:
        # Bush
        pygame.draw.circle(screen, (60, 120, 60), (fx, fy), 15)
        # Flowers
        for i in range(3):
            flower_x = fx + (i - 1) * 10
            flower_y = fy - 10
            pygame.draw.circle(screen, (255, 100, 150), (flower_x, flower_y), 4)
            pygame.draw.circle(screen, (255, 200, 0), (flower_x, flower_y), 2)


def main() -> None:
    """Run the character animation."""
    # Initialize Pygame
    pygame.init()
    pygame.mixer.init(
        frequency=AUDIO_SAMPLE_RATE, size=-16, channels=2, buffer=AUDIO_BUFFER_SIZE
    )

    # Set up display
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Character Animation with Audio")
    clock = pygame.time.Clock()

    # Initialize audio manager
    audio_manager = AudioManager()
    walking_sound = audio_manager.load_walking_sound()
    
    # Load collision sound effect
    try:
        collision_sound = pygame.mixer.Sound("assets/06_collide.wav")
        print("✓ Loaded collision sound effect")
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Could not load collision sound: {e}")
        collision_sound = None
    
    # Load meow sound effect
    try:
        meow_sound = pygame.mixer.Sound("assets/00_00_meow.wav")
        print("✓ Loaded meow sound effect")
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Could not load meow sound: {e}")
        meow_sound = None
    
    # Load spaceship sound effect
    try:
        spaceship_sound = pygame.mixer.Sound("assets/000_spaceship.wav")
        print("✓ Loaded spaceship sound effect")
    except (FileNotFoundError, pygame.error) as e:
        print(f"Warning: Could not load spaceship sound: {e}")
        spaceship_sound = None

    # Create characters with different voices
    char1 = Character(
        x=-50,
        y=SCREEN_HEIGHT - 200,
        color=BLUE,
        name="Character 1",
        voice="alloy",
    )
    char2 = Character(
        x=SCREEN_WIDTH + 10,
        y=SCREEN_HEIGHT - 200,
        color=RED,
        name="Character 2",
        voice="echo",
    )
    char2.direction = -1  # Moving left

    # Initialize animation controller
    animation = AnimationController(char1, char2, audio_manager, walking_sound, collision_sound, meow_sound, spaceship_sound)

    # Main game loop
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Update animation
        current_time = pygame.time.get_ticks()
        animation.update(current_time)

        # Auto-close when animation is finished
        if animation.phase == animation.AnimationPhase.FINISHED:
            # Wait 1 second after finishing, then close
            if animation.finished_time and current_time - animation.finished_time > 1000:
                running = False

        # Draw park background
        draw_park_background(screen)

        # Draw cat if in cat run phase
        if animation.phase == animation.AnimationPhase.CAT_RUN:
            cat_x = int(animation.cat_x)
            cat_y = SCREEN_HEIGHT - 150
            cat_scale = animation.cat_scale
            
            # Calculate scaled dimensions
            base_size = 40
            cat_width = int(base_size * cat_scale)
            cat_height = int(base_size * 0.7 * cat_scale)
            
            # Cat body (oval)
            body_rect = pygame.Rect(cat_x - cat_width // 2, cat_y - cat_height // 2,
                                   cat_width, cat_height)
            pygame.draw.ellipse(screen, (255, 140, 0), body_rect)  # Orange cat
            pygame.draw.ellipse(screen, (200, 100, 0), body_rect, max(1, int(2 * cat_scale)))
            
            # Cat head (circle)
            head_size = int(25 * cat_scale)
            head_x = cat_x + int(cat_width // 3)
            head_y = cat_y - int(cat_height // 3)
            pygame.draw.circle(screen, (255, 140, 0), (head_x, head_y), head_size)
            pygame.draw.circle(screen, (200, 100, 0), (head_x, head_y), head_size, max(1, int(2 * cat_scale)))
            
            # Cat ears (triangles)
            if cat_scale > 0.3:  # Only draw details when cat is close enough
                ear_size = int(10 * cat_scale)
                # Left ear
                left_ear = [
                    (head_x - int(12 * cat_scale), head_y - int(15 * cat_scale)),
                    (head_x - int(5 * cat_scale), head_y - int(5 * cat_scale)),
                    (head_x - int(15 * cat_scale), head_y - int(5 * cat_scale))
                ]
                pygame.draw.polygon(screen, (255, 140, 0), left_ear)
                pygame.draw.polygon(screen, (200, 100, 0), left_ear, max(1, int(2 * cat_scale)))
                
                # Right ear
                right_ear = [
                    (head_x + int(12 * cat_scale), head_y - int(15 * cat_scale)),
                    (head_x + int(5 * cat_scale), head_y - int(5 * cat_scale)),
                    (head_x + int(15 * cat_scale), head_y - int(5 * cat_scale))
                ]
                pygame.draw.polygon(screen, (255, 140, 0), right_ear)
                pygame.draw.polygon(screen, (200, 100, 0), right_ear, max(1, int(2 * cat_scale)))
                
                # Eyes (when close)
                if cat_scale > 0.6:
                    eye_size = max(2, int(3 * cat_scale))
                    pygame.draw.circle(screen, (0, 0, 0),
                                     (head_x - int(6 * cat_scale), head_y), eye_size)
                    pygame.draw.circle(screen, (0, 0, 0),
                                     (head_x + int(6 * cat_scale), head_y), eye_size)
            
            # Cat tail (curved line)
            tail_length = int(30 * cat_scale)
            tail_x = cat_x - int(cat_width // 2)
            tail_y = cat_y
            pygame.draw.line(screen, (255, 140, 0),
                           (tail_x, tail_y),
                           (tail_x - tail_length, tail_y - int(tail_length * 0.7)),
                           max(2, int(4 * cat_scale)))
            
            # Legs (simple lines)
            leg_length = int(15 * cat_scale)
            leg_spacing = int(10 * cat_scale)
            for i in range(2):
                leg_x = cat_x - int(cat_width // 4) + i * leg_spacing
                pygame.draw.line(screen, (255, 140, 0),
                               (leg_x, cat_y + cat_height // 2),
                               (leg_x, cat_y + cat_height // 2 + leg_length),
                               max(2, int(3 * cat_scale)))

        # Draw UFO and abduction beam if in abduction phase
        if animation.phase == animation.AnimationPhase.ALIEN_ABDUCTION:
            # Draw tractor beam
            if animation.beam_alpha > 0:
                beam_surface = pygame.Surface((100, SCREEN_HEIGHT), pygame.SRCALPHA)
                beam_color = (150, 255, 150, int(animation.beam_alpha))
                # Draw beam as a cone shape
                ufo_center_x = int(char2.get_center_x())
                beam_top_width = 60
                beam_bottom_width = 120
                
                for y in range(int(animation.ufo_y + 40), SCREEN_HEIGHT):
                    progress = (y - (animation.ufo_y + 40)) / (SCREEN_HEIGHT - (animation.ufo_y + 40))
                    width = int(beam_top_width + (beam_bottom_width - beam_top_width) * progress)
                    alpha = int(animation.beam_alpha * (1 - progress * 0.5))
                    pygame.draw.line(screen, (*beam_color[:3], alpha),
                                   (ufo_center_x - width // 2, y),
                                   (ufo_center_x + width // 2, y), 2)
            
            # Draw UFO
            ufo_x = int(char2.get_center_x())
            ufo_y = int(animation.ufo_y)
            
            # UFO dome (top)
            pygame.draw.ellipse(screen, (200, 200, 200),
                              (ufo_x - 50, ufo_y - 20, 100, 40))
            pygame.draw.ellipse(screen, (150, 150, 150),
                              (ufo_x - 50, ufo_y - 20, 100, 40), 2)
            
            # UFO base (bottom disc)
            pygame.draw.ellipse(screen, (180, 180, 180),
                              (ufo_x - 60, ufo_y + 10, 120, 30))
            pygame.draw.ellipse(screen, (100, 100, 100),
                              (ufo_x - 60, ufo_y + 10, 120, 30), 2)
            
            # UFO lights
            light_positions = [-40, -20, 0, 20, 40]
            for i, lx in enumerate(light_positions):
                light_color = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)][i]
                # Blinking effect
                if (current_time // 200 + i) % 2 == 0:
                    pygame.draw.circle(screen, light_color, (ufo_x + lx, ufo_y + 20), 5)
                else:
                    pygame.draw.circle(screen, (100, 100, 100), (ufo_x + lx, ufo_y + 20), 5)
            
            # UFO window
            pygame.draw.circle(screen, (100, 150, 200), (ufo_x, ufo_y), 15)
            pygame.draw.circle(screen, (50, 100, 150), (ufo_x, ufo_y), 15, 2)

        # Draw characters
        char1.draw(screen)
        char2.draw(screen)

        # Draw dialogue
        animation.draw_dialogue(screen)

        # Update display
        pygame.display.flip()
        clock.tick(FPS)

    # Clean up
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
